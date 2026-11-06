# genera los bustos del museo con funciones de distancia (sdf) y marching cubes
# uso: python Recursos/Herramientas/generar_bustos.py
# crea busto_1.npz, busto_2.npz, busto_3.npz y bronce.png
# necesita scipy y scikit-image (solo para generarlos, el juego no)
import os
import numpy as np
from scipy import ndimage
from skimage import measure
from PIL import Image

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SALIDA = os.path.join(RAIZ, "modelosObj", "Museo")
PASO = 0.014          # tamaño del voxel, mas chico = mas detalle

# primitivas sdf
def elipsoide(P, c, r):
    p = (P - np.asarray(c, np.float32)) / np.asarray(r, np.float32)
    k0 = np.linalg.norm(p, axis=-1)
    k1 = np.linalg.norm(p / np.asarray(r, np.float32), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def capsula(P, a, b, ra, rb=None):
    # sdf: negativo es adentro de la figura
    # capsula de a a b
    rb = ra if rb is None else rb
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    pa, ba = P - a, b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - (ra + (rb - ra) * h)


def esfera(P, c, r):
    return np.linalg.norm(P - np.asarray(c, np.float32), axis=-1) - r


def caja(P, c, b):
    q = np.abs(P - np.asarray(c, np.float32)) - np.asarray(b, np.float32)
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(np.max(q, axis=-1), 0)


def smin(a, b, k):
    # union suave
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    # interseccion suave
    return -smin(-a, -b, k)


def ruido3d(forma, celdas, semilla):
    # ruido 3d
    r = np.random.default_rng(semilla).random((celdas,) * 3).astype(np.float32)
    z = [s / celdas for s in forma]
    return ndimage.zoom(r, z, order=3)[: forma[0], : forma[1], : forma[2]] - 0.5


# escultura
def busto(variante):
    lim_min = np.array([-0.95, 0.40, -0.62], np.float32)
    lim_max = np.array([0.95, 2.36, 0.72], np.float32)
    ejes = [np.arange(lim_min[i], lim_max[i], PASO, dtype=np.float32) for i in range(3)]
    X, Y, Z = np.meshgrid(*ejes, indexing="ij")
    P = np.stack([X, Y, Z], axis=-1)
    forma = X.shape
    n_fino = ruido3d(forma, 70, 10 + variante)
    n_medio = ruido3d(forma, 28, 20 + variante)

    # cabeza
    d = elipsoide(P, (0, 1.80, 0.0), (0.335, 0.44, 0.405))                    # cráneo
    d = smin(d, elipsoide(P, (0, 1.53, 0.13), (0.245, 0.22, 0.25)), 0.12)      # mandíbula
    d = smin(d, elipsoide(P, (0, 1.43, 0.24), (0.11, 0.08, 0.10)), 0.08)       # mentón
    for s in (-1, 1):
        d = smin(d, elipsoide(P, (s * 0.19, 1.71, 0.24), (0.12, 0.085, 0.11)), 0.06)   # pómulos
        d = smin(d, elipsoide(P, (s * 0.335, 1.76, -0.02), (0.05, 0.125, 0.08)), 0.03)  # orejas
        d = smax(d, -esfera(P, (s * 0.13, 1.815, 0.40), 0.062), 0.04)          # cuencas de los ojos
        d = smin(d, esfera(P, (s * 0.13, 1.81, 0.335), 0.066), 0.015)           # ojos
        d = smin(d, elipsoide(P, (s * 0.13, 1.843, 0.375), (0.07, 0.02, 0.03)), 0.02)
    d = smin(d, capsula(P, (-0.22, 1.885, 0.325), (0.22, 1.885, 0.325), 0.05), 0.07)    # cejas
    d = smin(d, capsula(P, (0, 1.86, 0.385), (0, 1.70, 0.49), 0.035, 0.055), 0.05)      # nariz
    for s in (-1, 1):
        d = smin(d, esfera(P, (s * 0.042, 1.685, 0.445), 0.035), 0.03)          # aletas de la nariz
    d = smin(d, elipsoide(P, (0, 1.60, 0.405), (0.085, 0.022, 0.03)), 0.03)    # labio superior
    d = smin(d, elipsoide(P, (0, 1.565, 0.39), (0.075, 0.02, 0.028)), 0.03)    # labio inferior
    d = smax(d, -capsula(P, (-0.075, 1.583, 0.42), (0.075, 1.583, 0.42), 0.008), 0.01)  # boca

    # pelo
    if variante == 2:   # pelo corto hacia atras
        pelo = elipsoide(P, (0, 1.86, -0.05), (0.355, 0.40, 0.415))
        pelo = smax(pelo, -(Y - 1.98 + 0.35 * np.clip(Z, 0, None)), 0.05)
    else:
        pelo = elipsoide(P, (0, 1.87, -0.02), (0.36, 0.41, 0.43))
        pelo = smax(pelo, -(Y - 1.93 + 0.55 * np.clip(Z - 0.05, 0, None)), 0.05)
    pelo = smax(pelo, -(Y - 1.70 - 0.6 * np.clip(-Z, 0, None)), 0.05)           # nuca
    rizo = 0.035 if variante == 3 else 0.018
    pelo += rizo * n_fino + 0.01 * n_medio
    d = smin(d, pelo, 0.03)
    for s in (-1, 1):   # patillas
        d = smin(d, elipsoide(P, (s * 0.315, 1.70, 0.12), (0.035, 0.10, 0.05)) + 0.01 * n_fino, 0.03)

    # bigote y barba
    bigote = capsula(P, (-0.13, 1.60, 0.40), (0, 1.625, 0.455), 0.028, 0.034)
    bigote = smin(bigote, capsula(P, (0.13, 1.60, 0.40), (0, 1.625, 0.455), 0.028, 0.034), 0.03)
    d = smin(d, bigote + 0.012 * n_fino, 0.02)
    if variante == 3:
        barba = elipsoide(P, (0, 1.44, 0.20), (0.30, 0.27, 0.27))
        barba = smax(barba, -(1.585 - Y + 0.2 * np.abs(X)), 0.04)
        barba = smax(barba, -(Z - 0.0), 0.06)
        d = smin(d, barba + 0.03 * n_fino + 0.015 * n_medio, 0.04)

    # cuello, hombros y saco
    d = smin(d, capsula(P, (0, 1.10, -0.03), (0, 1.55, -0.01), 0.155), 0.08)
    torso = elipsoide(P, (0, 0.76, -0.05), (0.66, 0.40, 0.33))                        # caja torácica
    for s in (-1, 1):
        torso = smin(torso, capsula(P, (s * 0.10, 1.16, -0.05), (s * 0.56, 0.97, -0.07), 0.13, 0.15), 0.10)  # trapecios
        torso = smin(torso, elipsoide(P, (s * 0.60, 0.87, -0.06), (0.19, 0.17, 0.22)), 0.10)                   # deltoides
        torso = smin(torso, elipsoide(P, (s * 0.21, 0.86, 0.13), (0.25, 0.17, 0.17)), 0.10)                    # pecho
    cuello_saco = capsula(P, (-0.20, 1.17, 0.02), (0.20, 1.17, 0.02), 0.06)
    cuello_saco = smax(cuello_saco, -(Z + 0.05), 0.02)
    torso = smin(torso, cuello_saco, 0.04)
    for s in (-1, 1):   # solapas
        sol = capsula(P, (s * 0.10, 1.10, 0.22), (s * 0.22, 0.74, 0.31), 0.03)
        torso = smin(torso, sol, 0.03)
        torso = smax(torso, -capsula(P, (s * 0.07, 1.12, 0.24), (s * 0.18, 0.72, 0.34), 0.010), 0.008)
    for i, yb in enumerate((0.88, 0.72, 0.56)):   # botones
        torso = smin(torso, esfera(P, (0, yb, 0.335 - i * 0.012), 0.026), 0.01)
    torso += 0.004 * n_fino
    # corte del busto
    torso = smax(torso, elipsoide(P, (0, 0.45, -0.05), (0.86, 1.02, 0.52)), 0.04)
    d = smin(d, torso, 0.06)

    # base plana
    d = smax(d, -(Y - 0.45), 0.02)

    # textura del bronce
    d += 0.0025 * n_fino

    verts, caras, normales, _ = measure.marching_cubes(d, level=0.0, spacing=(PASO, PASO, PASO))
    verts = verts + lim_min
    normales = -normales if np.mean(np.sum(normales * (verts - verts.mean(0)), 1)) < 0 else normales

    # oclusion: revisa el campo a lo largo de la normal
    interp = ndimage.map_coordinates
    def campo(pts):
        # interpola el campo en cualquier punto
        idx = ((pts - lim_min) / PASO).T
        return interp(d, idx, order=1, mode="nearest")
    ao = np.zeros(len(verts), np.float32)
    for i, dist in enumerate((0.02, 0.05, 0.10, 0.18)):
        ao += (dist - np.clip(campo(verts + normales * dist), -1, dist)) / dist * (0.5 ** i)
    ao = np.clip(1.0 - 0.6 * ao, 0.0, 1.0)

    # normales hacia afuera
    t = verts[caras]
    nc = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    if np.mean(np.sum(nc * normales[caras].mean(1), 1)) < 0:
        caras = caras[:, ::-1]
    return verts.astype(np.float32), normales.astype(np.float32), ao, caras.astype(np.uint32)


def textura_bronce():
    # degradado de la patina oscura al bronce brillante
    x = np.linspace(0, 1, 256)
    claves = [(0.0, (20, 24, 19)), (0.5, (40, 37, 28)), (0.85, (72, 56, 38)), (1.0, (108, 80, 50))]
    col = np.zeros((256, 3))
    for c in range(3):
        col[:, c] = np.interp(x, [k[0] for k in claves], [k[1][c] for k in claves])
    img = np.repeat(col[None, :, :], 4, axis=0).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(SALIDA, "bronce.png"))


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    textura_bronce()
    for v in (1, 2, 3):
        verts, normales, ao, caras = busto(v)
        np.savez_compressed(os.path.join(SALIDA, f"busto_{v}.npz"), v=verts, n=normales, ao=ao, f=caras)
        print(f"busto_{v}: {len(caras)} triángulos")
