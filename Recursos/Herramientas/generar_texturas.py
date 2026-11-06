# genera las texturas de la hacienda a partir de las originales
# uso: python Recursos/Herramientas/generar_texturas.py
# crea pared_cal.jpg, techo_teja.jpg y piso_corredor.png
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
    # pared de cal
    img = Image.open(os.path.join(CARPETA, "Vinilopintado.jpeg")).convert("RGB")
    a = np.asarray(img, np.float32)
    h, w, _ = a.shape
    lum = a.mean(axis=2)
    suave = np.asarray(Image.fromarray(np.clip(lum, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(12)), np.float32)
    grano = (lum - suave) * 0.7                                   # grano del repello
    manchas = fbm(w, h, 4, 11) - 0.5                              # manchas de la cal
    base = np.array([240, 238, 230], np.float32)
    out = base + grano[..., None] + manchas[..., None] * np.array([14, 14, 18])
    # un poco sucio abajo
    y = np.linspace(0, 1, h)[:, None, None]
    out *= 1 - 0.05 * smoothstep(0.75, 1.0, y) * (0.5 + fbm(w, h, 16, 12)[..., None])
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(CARPETA, "pared_cal.jpg"), quality=92)


def techo():
    # tejas de barro
    img = Image.open(os.path.join(CARPETA, "techobarro.jpeg")).convert("RGB")
    a = np.asarray(img, np.float32) / 255
    h, w, _ = a.shape
    gris = a.mean(axis=2, keepdims=True)
    a = gris + (a - gris) * 0.72                                  # menos saturado
    a = a * np.array([0.84, 0.62, 0.54]) * 0.9                   # mas oscuro y rojizo
    # manchas de humedad
    m = smoothstep(0.55, 0.80, fbm(w, h, 9, 21))[..., None]
    a = a * (1 - 0.30 * m) + np.array([0.22, 0.20, 0.16]) * 0.30 * m
    variacion = 0.9 + 0.2 * fbm(w, h, 24, 22)[..., None]          # variacion entre tejas
    a = a * variacion
    Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).save(os.path.join(CARPETA, "techo_teja.jpg"), quality=92)


def piso():
    # piso de cemento del corredor
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
