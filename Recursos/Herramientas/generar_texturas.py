"""
Genera las texturas mejoradas de la hacienda a partir de las originales
(no las reemplaza: crea archivos nuevos en modelosObj/Hacienda/).

    python Recursos/Herramientas/generar_texturas.py

  pared_cal.jpg       pared encalada blanca (base: Vinilopintado.jpeg)
  techo_teja.jpg      teja de barro envejecida (base: techobarro.jpeg)
  piso_corredor.png   cemento gris azulado del corredor

Requiere numpy y Pillow.
"""
import os
import numpy as np
from PIL import Image, ImageFilter

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CARPETA = os.path.join(RAIZ, "modelosObj", "Hacienda")


def ruido(w, h, celdas, semilla):
    r = np.random.default_rng(semilla)
    base = r.random((celdas + 1, celdas + 1)).astype(np.float32)
    return np.asarray(Image.fromarray(base).resize((w, h), Image.BICUBIC))


def fbm(w, h, celdas, semilla, octavas=4):
    total, amp, suma = 0, 1.0, 0.0
    for i in range(octavas):
        total = total + amp * ruido(w, h, celdas * 2 ** i, semilla + i)
        suma += amp
        amp *= 0.5
    return total / suma


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def pared():
    img = Image.open(os.path.join(CARPETA, "Vinilopintado.jpeg")).convert("RGB")
    a = np.asarray(img, np.float32)
    h, w, _ = a.shape
    lum = a.mean(axis=2)
    suave = np.asarray(Image.fromarray(np.clip(lum, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(12)), np.float32)
    grano = (lum - suave) * 0.7                                   # textura fina del repello
    manchas = fbm(w, h, 4, 11) - 0.5                              # variación suave de la cal
    base = np.array([240, 238, 230], np.float32)
    out = base + grano[..., None] + manchas[..., None] * np.array([14, 14, 18])
    # Leve suciedad hacia abajo (salpicado de lluvia)
    y = np.linspace(0, 1, h)[:, None, None]
    out *= 1 - 0.05 * smoothstep(0.75, 1.0, y) * (0.5 + fbm(w, h, 16, 12)[..., None])
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(CARPETA, "pared_cal.jpg"), quality=92)


def techo():
    img = Image.open(os.path.join(CARPETA, "techobarro.jpeg")).convert("RGB")
    a = np.asarray(img, np.float32) / 255
    h, w, _ = a.shape
    gris = a.mean(axis=2, keepdims=True)
    a = gris + (a - gris) * 0.72                                  # menos saturado
    a = a * np.array([0.84, 0.62, 0.54]) * 0.9                   # barro cocido más oscuro y rojizo
    # Manchas de humedad / musgo y ennegrecido por el sol
    m = smoothstep(0.55, 0.80, fbm(w, h, 9, 21))[..., None]
    a = a * (1 - 0.30 * m) + np.array([0.22, 0.20, 0.16]) * 0.30 * m
    variacion = 0.9 + 0.2 * fbm(w, h, 24, 22)[..., None]          # tejas más claras / oscuras
    a = a * variacion
    Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).save(os.path.join(CARPETA, "techo_teja.jpg"), quality=92)


def piso():
    w = h = 256
    n = fbm(w, h, 8, 31) - 0.5
    r = np.random.default_rng(32).normal(0, 6, (h, w))
    base = np.array([118, 127, 136], np.float32)
    out = base + n[..., None] * 30 + r[..., None]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(CARPETA, "piso_corredor.png"))


if __name__ == "__main__":
    pared()
    techo()
    piso()
    print("Texturas generadas en", CARPETA)
