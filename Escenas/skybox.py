import os
import sys
import numpy as np
from OpenGL.GL import *
from PIL import Image

# Ruta base dinámica (soporte para .exe y script)
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# Función auxiliar para construir ruta absoluta
def recurso_path(*partes):
    return os.path.join(BASE_PATH, *partes)


def _skybox_path(nombre):
    return recurso_path("Recursos", "Imagenes", "Skybox", nombre)


# Sol / luna que vienen pintados en las imágenes frontales (centro x, centro y, radio
# incluyendo el resplandor, en píxeles de una imagen de 1024x1024). Se borran al cargar
# porque el sol y la luna reales se dibujan en Iluminacion.py y se mueven con la hora;
# si no, se veían dos soles / dos lunas.
_ASTRO_FRONTAL = (543, 853, 118)

RESOLUCION_TAPAS = 512      # tamaño de las caras superior e inferior generadas


# ---------------------------------------------------------------- Utilidades de imagen
def _leer(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def _borrar_disco(img, cx, cy, radio):
    """Rellena un disco interpolando horizontalmente entre sus bordes izquierdo y derecho
    (el cielo es un degradado vertical, así que el relleno queda invisible)."""
    h, w, _ = img.shape
    esc = w / 1024.0
    cx, cy, radio = cx * esc, cy * esc, radio * esc
    out = img.copy()
    for y in range(max(0, int(cy - radio)), min(h, int(cy + radio) + 1)):
        dy = y - cy
        if abs(dy) >= radio:
            continue
        mitad = np.sqrt(radio * radio - dy * dy)
        x0, x1 = int(max(0, cx - mitad - 2)), int(min(w - 1, cx + mitad + 2))
        if x1 - x0 < 2:
            continue
        t = np.linspace(0.0, 1.0, x1 - x0 + 1)[:, None]
        out[y, x0:x1 + 1] = img[y, x0] * (1 - t) + img[y, x1] * t
    return out


def _remuestrear(borde, n):
    """Cambia la longitud de un borde (k, 3) a (n, 3)."""
    x_old = np.linspace(0.0, 1.0, len(borde))
    x_new = np.linspace(0.0, 1.0, n)
    return np.stack([np.interp(x_new, x_old, borde[:, c]) for c in range(3)], axis=1)


def _suavizar(borde, sigma):
    radio = int(sigma * 3)
    k = np.exp(-0.5 * (np.arange(-radio, radio + 1) / sigma) ** 2)
    k /= k.sum()
    pad = np.pad(borde, ((radio, radio), (0, 0)), mode="edge")
    return np.stack([np.convolve(pad[:, c], k, mode="valid") for c in range(3)], axis=1)


def _coons(b0, b1, c0, c1):
    """Superficie de Coons: rellena un cuadrado conociendo sus 4 bordes.
    b0/b1 = bordes t=0 / t=1 (recorridos en s);  c0/c1 = bordes s=0 / s=1 (recorridos en t)."""
    n = len(b0)
    u = np.linspace(0.0, 1.0, n)[None, :, None]
    v = np.linspace(0.0, 1.0, n)[:, None, None]
    p00 = (b0[0] + c0[0]) / 2
    p10 = (b0[-1] + c1[0]) / 2
    p01 = (b1[0] + c0[-1]) / 2
    p11 = (b1[-1] + c1[-1]) / 2
    return ((1 - v) * b0[None] + v * b1[None] + (1 - u) * c0[:, None] + u * c1[:, None]
            - ((1 - u) * (1 - v) * p00 + u * (1 - v) * p10 + (1 - u) * v * p01 + u * v * p11))


def _tapa(b0, b1, c0, c1, n=RESOLUCION_TAPAS, estrellas=False):
    """Genera la cara superior/inferior del cubo a partir de los bordes de las 4 caras
    laterales: coincide exactamente en las uniones, sin el corte visible de antes."""
    exactos = [_remuestrear(b, n) for b in (b0, b1, c0, c1)]
    suaves = [_suavizar(b, n * 0.06) for b in exactos]
    img = _coons(*suaves)

    # Los detalles finos del borde (nubes) se conservan solo cerca de la unión
    d = np.linspace(0.0, 1.0, n)
    caida = np.clip(1.0 - d / 0.12, 0.0, 1.0) ** 2
    img += (exactos[0] - suaves[0])[None, :, :] * caida[:, None, None]
    img += (exactos[1] - suaves[1])[None, :, :] * caida[::-1][:, None, None]
    img += (exactos[2] - suaves[2])[:, None, :] * caida[None, :, None]
    img += (exactos[3] - suaves[3])[:, None, :] * caida[::-1][None, :, None]

    if estrellas:
        rng = np.random.default_rng(7)
        cantidad = int(n * n * 0.004)
        ys = rng.integers(0, n, cantidad)
        xs = rng.integers(0, n, cantidad)
        brillo = rng.random(cantidad) ** 3 * 200 + 25
        # Sin estrellas pegadas a los bordes para que la transición con las caras laterales sea suave
        dist_borde = np.minimum.reduce([ys, xs, n - 1 - ys, n - 1 - xs]) / n
        brillo *= np.clip((dist_borde - 0.06) / 0.25, 0.0, 1.0)
        for dy, dx, f in ((0, 0, 1.0), (1, 0, 0.35), (-1, 0, 0.35), (0, 1, 0.35), (0, -1, 0.35)):
            np.add.at(img, ((ys + dy) % n, (xs + dx) % n), (brillo * f)[:, None] * np.array([0.92, 0.95, 1.0]))

    return np.clip(img, 0, 255)


class Skybox:
    def __init__(self, size=50.0):
        self.size = size
        self.textures_dia = {}
        self.textures_noche = {}

        self.faces_dia = {
            "right": _skybox_path("Right_5.png"),
            "left": _skybox_path("Left_2.png"),
            "front": _skybox_path("Front_4.png"),
            "back": _skybox_path("Back_3.png"),
        }
        self.faces_noche = {
            "right": _skybox_path("NocheRight.jpeg"),
            "left": _skybox_path("NocheLeft.jpeg"),
            "front": _skybox_path("NocheFront.jpeg"),
            "back": _skybox_path("NocheBack.jpeg"),
        }

        self._cargar_set(self.faces_dia, self.textures_dia, estrellas=False)
        self._cargar_set(self.faces_noche, self.textures_noche, estrellas=True)

    # ------------------------------------------------------------ Carga
    def _cargar_set(self, faces, destino, estrellas):
        # "tex" = matriz tal como la muestrea OpenGL: fila 0 -> t=0 (abajo), columna 0 -> s=0
        tex = {}
        for nombre, path in faces.items():
            try:
                img = _leer(path)
                if nombre == "front":
                    img = _borrar_disco(img, *_ASTRO_FRONTAL)
                tex[nombre] = img[:, ::-1]          # espejo horizontal (orientación original)
            except Exception as e:
                print(f"Error cargando textura '{path}': {e}")

        if len(tex) == 4:
            f, b, l, r = tex["front"], tex["back"], tex["left"], tex["right"]
            # Cara superior: sus bordes son la última fila (t=1) de cada cara lateral
            tex["top"] = _tapa(f[-1], b[-1, ::-1], l[-1, ::-1], r[-1], estrellas=estrellas)
            # Cara inferior: sus bordes son la primera fila (t=0) de cada cara lateral
            tex["bottom"] = _tapa(b[0, ::-1], f[0], l[0], r[0, ::-1])
        else:
            print("⚠️ Faltan caras del skybox: no se generan el techo ni el piso del cielo")

        for nombre, datos in tex.items():
            destino[nombre] = self._subir(datos)

    @staticmethod
    def _subir(datos):
        datos = np.ascontiguousarray(np.clip(datos, 0, 255).astype(np.uint8))
        h, w, _ = datos.shape
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, datos)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # Evita las líneas visibles en las uniones del cubo
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_2D, 0)
        return texture_id

    # ------------------------------------------------------------ Límites del mundo
    def collides(self, pos, buffer=0.1):
        x, y, z = pos
        limit = self.size - buffer
        return abs(x) > limit or abs(y) > limit or abs(z) > limit

    # ------------------------------------------------------------ Dibujo
    def _draw_set(self, texturas, color):
        size = self.size

        def draw_face(tex, vertices):
            if tex not in texturas:
                return
            glBindTexture(GL_TEXTURE_2D, texturas[tex])
            glBegin(GL_QUADS)
            for coord, vert in zip([(0, 0), (1, 0), (1, 1), (0, 1)], vertices):
                glTexCoord2f(*coord)
                glVertex3f(*vert)
            glEnd()

        glColor4f(*color)
        draw_face("front",  [(-size, -size, -size), ( size, -size, -size), ( size,  size, -size), (-size,  size, -size)])
        draw_face("back",   [( size, -size,  size), (-size, -size,  size), (-size,  size,  size), ( size,  size,  size)])
        draw_face("left",   [(-size, -size,  size), (-size, -size, -size), (-size,  size, -size), (-size,  size,  size)])
        draw_face("right",  [( size, -size, -size), ( size, -size,  size), ( size,  size,  size), ( size,  size, -size)])
        draw_face("top",    [(-size,  size, -size), ( size,  size, -size), ( size,  size,  size), (-size,  size,  size)])
        draw_face("bottom", [(-size, -size,  size), ( size, -size,  size), ( size, -size, -size), (-size, -size, -size)])

    def draw(self, modo_dia=True, tinte=(1.0, 1.0, 1.0), centro=None):
        """modo_dia puede ser bool o un factor 0..1: con valores intermedios el cielo de
        día y el de noche se mezclan suavemente. 'centro' = posición de la cámara: el cielo
        se dibuja alrededor de ella para que parezca infinitamente lejano."""
        factor = max(0.0, min(1.0, float(modo_dia)))

        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        glEnable(GL_TEXTURE_2D)

        glPushMatrix()
        if centro is not None:
            glTranslatef(centro[0], centro[1], centro[2])

        r, g, b = tinte
        if factor < 1.0:
            self._draw_set(self.textures_noche, (r, g, b, 1.0))
        if factor > 0.0:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self._draw_set(self.textures_dia, (r, g, b, factor))

        glPopMatrix()
        glBindTexture(GL_TEXTURE_2D, 0)
        glDepthMask(GL_TRUE)
        glPopAttrib()
