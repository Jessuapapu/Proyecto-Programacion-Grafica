# nubes que se mueven con el viento
# son dos capas con una textura de ruido que se genera al iniciar
import math
import numpy as np
from OpenGL.GL import *

RESOLUCION = 512


# textura
def _ruido_periodico(n, celdas, rng):
    # ruido que se repite cada n pixeles
    g = rng.random((celdas, celdas)).astype(np.float32)
    x = np.arange(n, dtype=np.float32) * celdas / n
    i0 = np.floor(x).astype(int)
    f = x - i0
    f = f * f * (3 - 2 * f)
    i1 = (i0 + 1) % celdas
    fila0 = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i1] * f[None, :]
    fila1 = g[i1][:, i0] * (1 - f)[None, :] + g[i1][:, i1] * f[None, :]
    return fila0 * (1 - f)[:, None] + fila1 * f[:, None]


def _fbm(n, semilla, octavas=(4, 8, 16, 32, 64, 128)):
    # varias capas de ruido sumadas
    rng = np.random.default_rng(semilla)
    total = np.zeros((n, n), np.float32)
    amp, suma = 1.0, 0.0
    for celdas in octavas:
        total += _ruido_periodico(n, celdas, rng) * amp
        suma += amp
        amp *= 0.5
    total /= suma
    return (total - total.min()) / (total.max() - total.min())


def _textura_nubes(n=RESOLUCION, semilla=3, cobertura=0.50):
    # alfa = densidad, lo mas denso queda un poco mas oscuro
    ruido = _fbm(n, semilla)
    densidad = np.clip((ruido - cobertura) / 0.28, 0.0, 1.0)
    densidad = densidad * densidad * (3 - 2 * densidad)
    # relieve para que se vean con volumen
    relieve = np.clip((ruido - np.roll(ruido, (5, 5), (0, 1))) * 6.0, -1.0, 1.0)
    luz = np.clip(1.0 - 0.22 * densidad ** 1.5 + 0.12 * relieve, 0.68, 1.0)
    sombra = np.array([0.80, 0.84, 0.92], np.float32)
    rgb = luz[..., None] * (sombra + (1.0 - sombra) * luz[..., None])
    alfa = np.clip(densidad * 1.05, 0.0, 1.0) ** 0.85
    return np.dstack([rgb, alfa]).astype(np.float32)


def _subir_con_mipmaps(rgba):
    # sube la textura con mipmaps hechos a mano para que no parpadeen de lejos
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    nivel, img = 0, rgba
    while True:
        datos = np.ascontiguousarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        h, w = datos.shape[:2]
        glTexImage2D(GL_TEXTURE_2D, nivel, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, datos)
        if w == 1 and h == 1:
            break
        img = img.reshape(h // 2, 2, w // 2, 2, 4).mean(axis=(1, 3)) if h > 1 and w > 1 else img[:1, :1]
        nivel += 1
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glBindTexture(GL_TEXTURE_2D, 0)
    return tex


# boveda
def _boveda(radio, altura, caida, anillos=28, segmentos=56):
    # disco que baja en los bordes, la opacidad se va perdiendo hacia el horizonte
    pos, fade = [], []
    for i in range(anillos + 1):
        r = radio * (i / anillos) ** 1.15
        for j in range(segmentos):
            a = 2 * math.pi * j / segmentos
            t = r / radio
            pos.append((r * math.cos(a), altura - caida * t * t, r * math.sin(a)))
            fade.append(1.0 - min(1.0, max(0.0, (t - 0.45) / 0.55)) ** 1.6)
    idx = []
    for i in range(anillos):
        for j in range(segmentos):
            a, b = i * segmentos + j, i * segmentos + (j + 1) % segmentos
            c, d = a + segmentos, b + segmentos
            idx += [a, c, b, b, c, d]
    return (np.array(pos, np.float32), np.array(fade, np.float32), np.array(idx, np.uint32))


class _Capa:
    def __init__(self, radio, altura, caida, escala, viento, opacidad, giro):
        self.pos, self.fade, self.idx = _boveda(radio, altura, caida)
        c, s = math.cos(giro), math.sin(giro)
        x, z = self.pos[:, 0], self.pos[:, 2]
        # uv rotadas para que las capas no coincidan
        self.uv_base = (np.stack([x * c - z * s, x * s + z * c], 1) / escala).astype(np.float32)
        self.viento = np.array(viento, np.float32) / escala     # por segundo
        self.opacidad = opacidad
        self.colores = np.zeros((len(self.pos), 4), np.float32)

    def dibujar(self, tiempo, color):
        # mover las uv con el tiempo
        uv = np.ascontiguousarray(self.uv_base + (self.viento * tiempo) % 1.0)
        self.colores[:, :3] = color[:3]
        self.colores[:, 3] = self.fade * self.opacidad * color[3]
        glVertexPointer(3, GL_FLOAT, 0, self.pos)
        glTexCoordPointer(2, GL_FLOAT, 0, uv)
        glColorPointer(4, GL_FLOAT, 0, self.colores)
        glDrawElements(GL_TRIANGLES, len(self.idx), GL_UNSIGNED_INT, self.idx)


class Nubes:
    def __init__(self, velocidad=1.0):
        self.velocidad = velocidad
        self.textura = _subir_con_mipmaps(_textura_nubes())
        # capa alta lenta y capa baja mas rapida
        self.capas = [
            _Capa(radio=600, altura=95, caida=80, escala=230, viento=(5.0, 1.6), opacidad=0.95, giro=0.0),
            _Capa(radio=560, altura=75, caida=70, escala=120, viento=(7.5, 3.2), opacidad=0.55, giro=1.1),
        ]

    @staticmethod
    def _color(estado):
        # color segun la hora
        fd = estado['factor_dia']
        sol = estado['color_sol']
        altura_sol = estado['dir_sol'][1]
        dorado = 1.0 - min(1.0, max(0.0, (altura_sol - 0.02) / 0.45))
        dia = [1.0 * (1 - dorado) + (0.55 + 0.45 * c) * dorado for c in sol]
        noche = [0.20, 0.23, 0.32]
        rgb = [noche[i] * (1 - fd) + dia[i] * fd for i in range(3)]
        alfa = 0.55 + 0.45 * fd
        return rgb + [alfa]

    def dibujar(self, tiempo, centro, estado):
        # dibujar despues del cielo y antes de la escena
        color = self._color(estado)
        t = tiempo * self.velocidad

        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_TEXTURE_BIT)
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_CULL_FACE)
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.textura)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        # por si quedo un vbo enlazado
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)

        glPushMatrix()
        glTranslatef(centro[0], centro[1], centro[2])
        for capa in self.capas:
            capa.dibujar(t, color)
        glPopMatrix()

        glBindTexture(GL_TEXTURE_2D, 0)
        glPopClientAttrib()
        glPopAttrib()

    def liberar(self):
        if self.textura:
            glDeleteTextures([self.textura])
            self.textura = 0
