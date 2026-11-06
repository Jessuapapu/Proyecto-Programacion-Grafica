# sala de los heroes: bustos, retratos, letrero y vitrinas
# todo se arma con codigo usando los datos de museo.json
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from OpenGL.GL import *

from Clases.Modelo import Modelos
from Escenas import Vitrinas

FUENTES = ["georgiab.ttf", "timesbd.ttf", "DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf",
           "arialbd.ttf", "DejaVuSans-Bold.ttf"]
CARPETAS_FUENTES = ["", "C:/Windows/Fonts", "/usr/share/fonts/truetype/dejavu",
                    "/usr/share/fonts/truetype/liberation", "/System/Library/Fonts/Supplemental"]

COLORES = {
    "Marmol": (1.0, 1.0, 1.0),
    "Bronce": (1.0, 1.0, 1.0),
    "Marco": (0.10, 0.08, 0.07),
    "Carton": (0.93, 0.91, 0.86),
}

ALTO_PEDESTAL = 3.4     # altura del pedestal


# textos y texturas
def _fuente(tam):
    # busca una fuente que exista en la compu
    for nombre in FUENTES:
        for carpeta in CARPETAS_FUENTES:
            try:
                return ImageFont.truetype(os.path.join(carpeta, nombre) if carpeta else nombre, tam)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=tam)
    except TypeError:
        return ImageFont.load_default()


def _texto_centrado(img, lineas, color, y0, tam, interlineado=1.25, margen=24):
    # escribe lineas centradas, si no caben baja el tamaño de la letra
    d = ImageDraw.Draw(img)
    while True:
        f = _fuente(tam)
        mas_ancha = max(d.textbbox((0, 0), l, font=f)[2] - d.textbbox((0, 0), l, font=f)[0] for l in lineas)
        if mas_ancha <= img.width - 2 * margen or tam <= 10:
            break
        tam -= 2
    y = y0
    for linea in lineas:
        caja = d.textbbox((0, 0), linea, font=f)
        ancho = caja[2] - caja[0]
        d.text(((img.width - ancho) / 2 - caja[0], y), linea, font=f, fill=color)
        y += int(tam * interlineado)
    return img


def _subir(img):
    # sube una imagen de PIL como textura
    img = img.convert("RGBA")
    datos = img.tobytes()
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, datos)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    try:
        glGenerateMipmap(GL_TEXTURE_2D)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    except Exception:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glBindTexture(GL_TEXTURE_2D, 0)
    return tex


# geometria
def _quad(p0, p1, p2, p3, uv=((0, 1), (1, 1), (1, 0), (0, 0))):
    # cuadrado con los 4 puntos en orden antihorario
    p = [np.asarray(v, float) for v in (p0, p1, p2, p3)]
    n = np.cross(p[1] - p[0], p[3] - p[0])
    n /= np.linalg.norm(n) + 1e-12
    out = []
    for i in (0, 1, 2, 0, 2, 3):
        out.append(list(p[i]) + list(uv[i]) + list(n))
    return np.array(out, np.float32)


def _caja(cx, cy, cz, sx, sy, sz, escala_uv=1.0):
    # caja con la base en cy
    x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy, cy + sy, cz - sz / 2, cz + sz / 2
    u = escala_uv
    caras = [
        _quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), ((0, sy * u), (sx * u, sy * u), (sx * u, 0), (0, 0))),
        _quad((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), ((0, sy * u), (sx * u, sy * u), (sx * u, 0), (0, 0))),
        _quad((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0), ((0, sy * u), (sz * u, sy * u), (sz * u, 0), (0, 0))),
        _quad((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), ((0, sy * u), (sz * u, sy * u), (sz * u, 0), (0, 0))),
        _quad((x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0), ((0, sz * u), (sx * u, sz * u), (sx * u, 0), (0, 0))),
        _quad((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), ((0, sz * u), (sx * u, sz * u), (sx * u, 0), (0, 0))),
    ]
    return np.concatenate(caras)


def _tris_a_datos(tris):
    # triangulos a vertices de 8 valores
    tris = np.asarray(tris, np.float64)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    out = np.zeros((len(tris), 3, 8), np.float32)
    out[..., 0:3] = tris
    out[..., 5:8] = n[:, None, :]
    return out.reshape(-1, 8)


def _transformar(datos, x, y, z, rot_grados):
    # rotar en y y mover a x, y, z
    a = math.radians(rot_grados)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)
    out = datos.copy()
    out[:, 0:3] = datos[:, 0:3] @ R.T + np.array([x, y, z], np.float32)
    out[:, 5:8] = datos[:, 5:8] @ R.T
    return out


def _busto(carpeta, variante):
    # carga un busto de generar_bustos.py
    # en u va la oclusion, la textura bronce.png la pinta mas oscura en los huecos
    d = np.load(os.path.join(carpeta, f"busto_{int(variante)}.npz"))
    v, n, ao, f = d["v"], d["n"], d["ao"], d["f"].ravel()
    out = np.zeros((len(f), 8), np.float32)
    out[:, 0:3] = v[f]
    out[:, 3] = np.clip(ao[f], 0.02, 0.98)
    out[:, 4] = 0.5
    out[:, 5:8] = n[f]
    return out


def _pedestal():
    # pedestal de marmol, devuelve el frente aparte para ponerle el nombre
    b, t, H = 0.66, 0.74, ALTO_PEDESTAL - 0.3
    y0 = 0.15
    frente = _quad((-b, y0, b), (b, y0, b), (t, y0 + H, t), (-t, y0 + H, t))
    lados = [
        _quad((b, y0, -b), (-b, y0, -b), (-t, y0 + H, -t), (t, y0 + H, -t), ((0, 1.2), (0.6, 1.2), (0.6, 0), (0, 0))),
        _quad((-b, y0, -b), (-b, y0, b), (-t, y0 + H, t), (-t, y0 + H, -t), ((0, 1.2), (0.6, 1.2), (0.6, 0), (0, 0))),
        _quad((b, y0, b), (b, y0, -b), (t, y0 + H, -t), (t, y0 + H, t), ((0, 1.2), (0.6, 1.2), (0.6, 0), (0, 0))),
    ]
    resto = np.concatenate(lados + [_caja(0, 0, 0, 1.55, 0.15, 1.55, 0.35),
                                    _caja(0, y0 + H, 0, 1.70, 0.15, 1.70, 0.35)])
    return resto, frente


class Museo:

    def __init__(self, carpeta):
        self.carpeta = carpeta
        self.modelo = None
        self.vidrio = None
        self._obstaculos = []      # x, z, radio, y_max
        self._cajas = []           # x0, x1, z0, z1, y_max

    def cargarmodelos(self):
        # lee museo.json y arma la sala
        with open(os.path.join(self.carpeta, "museo.json"), "r", encoding="utf-8") as f:
            cfg = json.load(f)
        piso = float(cfg.get("piso_y", -2.2))
        datos, colores, texturas = {}, dict(COLORES), {}

        # geometria por material
        def agregar(mat, arr):
            datos.setdefault(mat, []).append(arr)

        marmol = Image.open(os.path.join(self.carpeta, "marmol.jpg")).convert("RGB")
        texturas["Marmol"] = _subir(marmol)
        texturas["Bronce"] = _subir(Image.open(os.path.join(self.carpeta, "bronce.png")))

        # bustos
        resto, frente = _pedestal()
        for i, b in enumerate(cfg.get("bustos", [])):
            x, z, rot = float(b["x"]), float(b["z"]), float(b.get("rot", 0))
            agregar("Marmol", _transformar(resto, x, piso, z, rot))
            mat = f"Placa_busto_{i}"
            agregar(mat, _transformar(frente, x, piso, z, rot))
            # frente del pedestal con el nombre
            placa = marmol.resize((300, 670))
            _texto_centrado(placa, b["nombre"], (60, 42, 26), 60, 40, margen=20)
            texturas[mat] = _subir(placa)
            colores[mat] = (1.0, 1.0, 1.0)
            # la base del busto esta en y = 0.45
            agregar("Bronce", _transformar(_busto(self.carpeta, b.get("variante", i + 1)),
                                           x, piso + ALTO_PEDESTAL + 0.15 - 0.45, z, rot))
            self._obstaculos.append((x, z, 1.1, piso + ALTO_PEDESTAL + 2.5))

        # retratos con marco y ficha
        for i, r in enumerate(cfg.get("retratos", [])):
            img = Image.open(os.path.join(self.carpeta, r["imagen"])).convert("RGB")
            alto = float(r.get("alto", 3.0))
            ancho = alto * img.width / img.height
            x, y, z, rot = float(r["x"]), float(r["y"]), float(r["z"]), float(r.get("rot", 0))
            mat = f"Retrato_{i}"
            texturas[mat] = _subir(img)
            colores[mat] = (1.0, 1.0, 1.0)
            # se recorta un poco el borde de la foto
            w2, h2, m = ancho / 2, alto / 2, 0.03
            foto = _quad((-w2, -h2, 0.09), (w2, -h2, 0.09), (w2, h2, 0.09), (-w2, h2, 0.09),
                         ((m, 1 - m), (1 - m, 1 - m), (1 - m, m), (m, m)))
            agregar(mat, _transformar(foto, x, y, z, rot))
            g = 0.16   # grosor del marco
            marco = np.concatenate([
                _caja(0, h2, 0.06, ancho + 2 * g, g, 0.12),
                _caja(0, -h2 - g, 0.06, ancho + 2 * g, g, 0.12),
                _caja(-w2 - g / 2, -h2, 0.06, g, alto, 0.12),
                _caja(w2 + g / 2, -h2, 0.06, g, alto, 0.12),
                _caja(0, -h2, 0.01, ancho, alto, 0.06),
            ])
            agregar("Marco", _transformar(marco, x, y, z, rot))
            # ficha abajo del retrato
            ficha_mat = f"Ficha_{i}"
            fw, fh = 2.4, 0.62
            ficha = _quad((-fw / 2, -fh / 2, 0.05), (fw / 2, -fh / 2, 0.05), (fw / 2, fh / 2, 0.05), (-fw / 2, fh / 2, 0.05))
            yf = y - h2 - g - 0.75
            agregar(ficha_mat, _transformar(ficha, x, yf, z, rot))
            agregar("Marco", _transformar(_caja(0, -fh / 2, 0.0, fw + 0.06, fh, 0.05), x, yf, z, rot))
            tarjeta = Image.new("RGB", (480, 124), (238, 234, 224))
            lineas = r["nombre"] if isinstance(r["nombre"], list) else [r["nombre"]]
            _texto_centrado(tarjeta, lineas, (45, 35, 30), 16 if len(lineas) > 1 else 40, 38)
            texturas[ficha_mat] = _subir(tarjeta)
            colores[ficha_mat] = (1.0, 1.0, 1.0)

        # letrero
        t = cfg.get("titulo")
        if t:
            ancho = float(t.get("ancho", 12.0))
            alto = ancho * 0.16
            x, y, z, rot = float(t["x"]), float(t["y"]), float(t["z"]), float(t.get("rot", 0))
            letrero = Image.new("RGB", (1300, 208), (92, 38, 30))
            d = ImageDraw.Draw(letrero)
            d.rectangle((8, 8, 1291, 199), outline=(205, 170, 110), width=4)
            _texto_centrado(letrero, t["texto"][:1], (240, 226, 196), 42, 64)
            if len(t["texto"]) > 1:
                _texto_centrado(letrero, t["texto"][1:], (215, 190, 150), 128, 40)
            texturas["Letrero"] = _subir(letrero)
            colores["Letrero"] = (1.0, 1.0, 1.0)
            q = _quad((-ancho / 2, -alto / 2, 0.08), (ancho / 2, -alto / 2, 0.08),
                      (ancho / 2, alto / 2, 0.08), (-ancho / 2, alto / 2, 0.08))
            agregar("Letrero", _transformar(q, x, y, z, rot))
            agregar("Marco", _transformar(_caja(0, -alto / 2 - 0.05, 0.02, ancho + 0.1, alto + 0.1, 0.06), x, y, z, rot))

        # vitrinas
        vidrios = []
        colores.update({k: v for k, v in Vitrinas.COLORES.items() if k != "Vidrio"})
        for i, v in enumerate(cfg.get("vitrinas", [])):
            opacos, vidrio, tarjetas, caja_col = Vitrinas.construir(
                float(v["x"]), piso, float(v["z"]), float(v.get("rot", 0)),
                n_revolveres=int(v.get("revolveres", 6)), n_bayonetas=int(v.get("bayonetas", 3)),
                n_fusiles=int(v.get("fusiles", 3)), semilla=i)
            for mat, tris in opacos.items():
                agregar(mat, _tris_a_datos(tris))
            vidrios.append(_tris_a_datos(vidrio))
            for j, (esq, texto) in enumerate(tarjetas):
                mat = f"Tarjeta_{i}_{j}"
                ancho_px = int(260 * np.linalg.norm(esq[1] - esq[0]) / 0.3)
                img = Image.new("RGB", (max(ancho_px, 120), 120 if len(texto) == 1 else 40 + 36 * len(texto)), (246, 244, 238))
                _texto_centrado(img, texto, (35, 30, 28), 12, 34 if len(texto) == 1 else 28, margen=10)
                texturas[mat] = _subir(img)
                colores[mat] = (1.0, 1.0, 1.0)
                agregar(mat, _quad(*esq))
            self._cajas.append(caja_col)

        # subir todo y poner las texturas
        datos = {k: np.concatenate(v) for k, v in datos.items()}
        self.modelo = Modelos.desde_datos(datos, colores)
        for mat, tex in texturas.items():
            if mat in self.modelo.materiales:
                self.modelo.materiales[mat]["tex_id"] = tex
        # brillo de los metales y el marmol
        bronce = self.modelo.materiales.get("Bronce")
        if bronce:
            bronce["ks"] = [0.9, 0.75, 0.55]
            bronce["ns"] = 220.0
        if "Marmol" in self.modelo.materiales:
            self.modelo.materiales["Marmol"]["ks"] = [0.25, 0.25, 0.25]
        for mat, ks, ns in (("Oro", [0.9, 0.75, 0.45], 240.0), ("MetalArma", [0.55, 0.55, 0.55], 300.0),
                            ("MetalOxido", [0.2, 0.18, 0.16], 120.0), ("Terciopelo", [0.03, 0.02, 0.02], 16.0)):
            if mat in self.modelo.materiales:
                self.modelo.materiales[mat]["ks"] = ks
                self.modelo.materiales[mat]["ns"] = ns
        # vidrio aparte porque es transparente
        if vidrios:
            self.vidrio = Modelos.desde_datos({"Vidrio": np.concatenate(vidrios)}, {"Vidrio": Vitrinas.COLORES["Vidrio"]})
            self.vidrio.materiales["Vidrio"]["alfa"] = 0.16
            self.vidrio.materiales["Vidrio"]["ks"] = [1.0, 1.0, 1.0]
            self.vidrio.materiales["Vidrio"]["ns"] = 500.0

    def collides(self, punto):
        # pedestales como circulos y vitrinas como rectangulos
        x, y, z = punto
        for ox, oz, r, ymax in self._obstaculos:
            if (x - ox) ** 2 + (z - oz) ** 2 < r * r and y < ymax:
                return True
        for x0, x1, z0, z1, ymax in self._cajas:
            if x0 <= x <= x1 and z0 <= z <= z1 and y < ymax:
                return True
        return False

    def draw(self):
        if self.modelo is not None:
            self.modelo.draw()

    def draw_transparente(self):
        # vidrios al final con blending y sin escribir profundidad
        if self.vidrio is None:
            return
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_ENABLE_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        self.vidrio.draw()
        glPopAttrib()

    def liberar(self):
        for m in (self.modelo, self.vidrio):
            if m is not None:
                m.liberar()
