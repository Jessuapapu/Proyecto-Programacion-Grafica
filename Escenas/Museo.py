"""
Sala de los Héroes: bustos de bronce sobre pedestales de mármol con sus nombres,
retratos enmarcados con fichas y un letrero, dentro de la casa hacienda.

Todo se arma por código (estilo low-poly) a partir de modelosObj/Museo/museo.json,
donde se pueden cambiar los nombres, las posiciones y las imágenes.
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from OpenGL.GL import *

from Clases.Modelo import Modelos

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

ALTO_PEDESTAL = 3.4


# ------------------------------------------------------------------ Texto y texturas
def _fuente(tam):
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
    d = ImageDraw.Draw(img)
    # Reduce la letra hasta que la línea más larga quepa en la imagen
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
    """Sube una imagen de PIL como textura (fila superior primero, igual que Modelo.py)."""
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


# ------------------------------------------------------------------ Geometría
def _quad(p0, p1, p2, p3, uv=((0, 1), (1, 1), (1, 0), (0, 0))):
    """Cuadrilátero p0-p1-p2-p3 (antihorario visto de frente). uv por defecto:
    p0 abajo-izq, p1 abajo-der, p2 arriba-der, p3 arriba-izq (imagen derecha)."""
    p = [np.asarray(v, float) for v in (p0, p1, p2, p3)]
    n = np.cross(p[1] - p[0], p[3] - p[0])
    n /= np.linalg.norm(n) + 1e-12
    out = []
    for i in (0, 1, 2, 0, 2, 3):
        out.append(list(p[i]) + list(uv[i]) + list(n))
    return np.array(out, np.float32)


def _caja(cx, cy, cz, sx, sy, sz, escala_uv=1.0):
    """Caja con base en cy. Devuelve las 6 caras (N, 8)."""
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
    tris = np.asarray(tris, np.float64)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    out = np.zeros((len(tris), 3, 8), np.float32)
    out[..., 0:3] = tris
    out[..., 5:8] = n[:, None, :]
    return out.reshape(-1, 8)


def _transformar(datos, x, y, z, rot_grados):
    a = math.radians(rot_grados)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)
    out = datos.copy()
    out[:, 0:3] = datos[:, 0:3] @ R.T + np.array([x, y, z], np.float32)
    out[:, 5:8] = datos[:, 5:8] @ R.T
    return out


def _busto(carpeta, variante):
    """Busto esculpido (ver Recursos/Herramientas/generar_bustos.py): malla suave con
    normales por vértice. La coordenada u guarda la oclusión ambiental, que la textura
    bronce.png convierte en pátina oscura en los huecos y bronce claro en lo saliente."""
    d = np.load(os.path.join(carpeta, f"busto_{int(variante)}.npz"))
    v, n, ao, f = d["v"], d["n"], d["ao"], d["f"].ravel()
    out = np.zeros((len(f), 8), np.float32)
    out[:, 0:3] = v[f]
    out[:, 3] = np.clip(ao[f], 0.02, 0.98)
    out[:, 4] = 0.5
    out[:, 5:8] = n[f]
    return out


def _pedestal():
    """Pedestal de mármol: cuerpo algo más ancho arriba, zócalo y tapa. Base en el origen.
    Devuelve (resto, frente) para poder ponerle al frente la textura con el nombre."""
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
        self._obstaculos = []      # (x, z, radio, y_max)

    def cargarmodelos(self):
        with open(os.path.join(self.carpeta, "museo.json"), "r", encoding="utf-8") as f:
            cfg = json.load(f)
        piso = float(cfg.get("piso_y", -2.2))
        datos, colores, texturas = {}, dict(COLORES), {}

        def agregar(mat, arr):
            datos.setdefault(mat, []).append(arr)

        marmol = Image.open(os.path.join(self.carpeta, "marmol.jpg")).convert("RGB")
        texturas["Marmol"] = _subir(marmol)
        texturas["Bronce"] = _subir(Image.open(os.path.join(self.carpeta, "bronce.png")))

        # ---------------- Bustos sobre pedestales
        resto, frente = _pedestal()
        for i, b in enumerate(cfg.get("bustos", [])):
            x, z, rot = float(b["x"]), float(b["z"]), float(b.get("rot", 0))
            agregar("Marmol", _transformar(resto, x, piso, z, rot))
            mat = f"Placa_busto_{i}"
            agregar(mat, _transformar(frente, x, piso, z, rot))
            placa = marmol.resize((300, 670))
            _texto_centrado(placa, b["nombre"], (60, 42, 26), 60, 40, margen=20)
            texturas[mat] = _subir(placa)
            colores[mat] = (1.0, 1.0, 1.0)
            # La base del busto esculpido está en y = 0.45
            agregar("Bronce", _transformar(_busto(self.carpeta, b.get("variante", i + 1)),
                                           x, piso + ALTO_PEDESTAL + 0.15 - 0.45, z, rot))
            self._obstaculos.append((x, z, 1.1, piso + ALTO_PEDESTAL + 2.5))

        # ---------------- Retratos enmarcados con su ficha
        for i, r in enumerate(cfg.get("retratos", [])):
            img = Image.open(os.path.join(self.carpeta, r["imagen"])).convert("RGB")
            alto = float(r.get("alto", 3.0))
            ancho = alto * img.width / img.height
            x, y, z, rot = float(r["x"]), float(r["y"]), float(r["z"]), float(r.get("rot", 0))
            mat = f"Retrato_{i}"
            texturas[mat] = _subir(img)
            colores[mat] = (1.0, 1.0, 1.0)
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
            # Ficha debajo del retrato
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

        # ---------------- Letrero de la sala
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

        datos = {k: np.concatenate(v) for k, v in datos.items()}
        self.modelo = Modelos.desde_datos(datos, colores)
        for mat, tex in texturas.items():
            if mat in self.modelo.materiales:
                self.modelo.materiales[mat]["tex_id"] = tex
        bronce = self.modelo.materiales.get("Bronce")
        if bronce:
            bronce["ks"] = [0.9, 0.75, 0.55]
            bronce["ns"] = 220.0
        if "Marmol" in self.modelo.materiales:
            self.modelo.materiales["Marmol"]["ks"] = [0.25, 0.25, 0.25]

    def collides(self, punto):
        x, y, z = punto
        for ox, oz, r, ymax in self._obstaculos:
            if (x - ox) ** 2 + (z - oz) ** 2 < r * r and y < ymax:
                return True
        return False

    def draw(self):
        if self.modelo is not None:
            self.modelo.draw()

    def liberar(self):
        if self.modelo is not None:
            self.modelo.liberar()
