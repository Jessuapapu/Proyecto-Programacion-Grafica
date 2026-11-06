"""
Generador del mapa (terreno, texturas del suelo y vegetación).

No hace falta ejecutarlo para jugar: sus resultados ya están en modelosObj/Terreno/.
Sirve para regenerar el mapa si se cambian los parámetros de abajo.

    python Recursos/Herramientas/generar_mapa.py

Genera:
    modelosObj/Terreno/altura.npy           alturas del terreno (grilla)
    modelosObj/Terreno/terreno_color.png    color del suelo (RGB) + cantidad de pasto (A)
    modelosObj/Terreno/terreno_detalle.png  detalle fino repetible (R = pasto, G = tierra)
    modelosObj/Terreno/vegetacion.json      posición de árboles y arbustos
    modelosObj/colision_hacienda.obj        colisiones de la hacienda sin el terreno viejo

Requiere solo numpy y Pillow.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELOS = os.path.join(RAIZ, "modelosObj")
SALIDA = os.path.join(MODELOS, "Terreno")

# ------------------------------------------------------------------ Parámetros
EXTENSION = 420.0          # el terreno va de -EXTENSION a +EXTENSION en X y Z
PASO_MALLA = 2.5           # separación entre vértices del terreno
RES_COLOR = 2048           # resolución de la textura de color del suelo
NIVEL_BASE = -3.05         # altura del suelo plano donde están la casa, corrales, etc.
SEMILLA = 1856             # año de la batalla de San Jacinto

# Explanadas de tierra roja (x0, x1, z0, z1) y caminos (polilíneas de puntos x, z)
EXPLANADAS = [
    (-24.0, 38.0, -48.0, 38.0),    # alrededor de la casa
    (38.0, 100.0, -48.0, 8.0),     # explanada grande junto a la casa
]
CAMINOS = [
    [(8, 38), (10, 70), (22, 120), (12, 180), (34, 250), (70, 330), (95, 420)],          # entrada
    [(20, -48), (56, -56), (56, -100), (56, -150), (82, -230), (125, -330), (150, -420)],  # corrales
    [(-24, 6), (-55, 10), (-70, 30)],                                                      # hacia el cercado
]
ANCHO_CAMINO = 5.0

# Colinas dentro del área jugable (x, z, altura, radio)
COLINAS = [(165, 195, 16, 55), (-150, 205, 12, 50), (195, -165, 14, 50),
           (-215, -205, 11, 45), (205, 40, 8, 40), (-30, -205, 9, 45)]

# Árboles viejos que se conservan (se reemplazan por árboles nuevos en el mismo lugar)
ARBOLES_FIJOS = [(-25.1, -31.2), (-51.9, -1.6), (102.6, 99.2), (55.8, 111.1)]


# ------------------------------------------------------------------ Utilidades
rng = np.random.default_rng(SEMILLA)


def ruido(res, escala_celdas, semilla):
    """Ruido suave: una grilla aleatoria pequeña ampliada con interpolación bicúbica."""
    r = np.random.default_rng(semilla)
    base = r.random((escala_celdas + 3, escala_celdas + 3)).astype(np.float32)
    img = Image.fromarray(base).resize((res + 2 * res // escala_celdas,) * 2, Image.BICUBIC)
    a = np.asarray(img)
    o = res // escala_celdas
    return a[o:o + res, o:o + res]


def fbm(res, octavas, base_celdas, semilla, persistencia=0.5):
    total = np.zeros((res, res), np.float32)
    amp, suma = 1.0, 0.0
    for i in range(octavas):
        total += amp * ruido(res, base_celdas * 2 ** i, semilla + i * 101)
        suma += amp
        amp *= persistencia
    return total / suma


def suavizar(a, sigma):
    """Desenfoque gaussiano separable (solo numpy)."""
    r = int(sigma * 3)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    a = np.pad(a, r, mode="edge")
    a = np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 0, a)
    a = np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 1, a)
    return a


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def coords(res):
    c = np.linspace(-EXTENSION, EXTENSION, res, dtype=np.float32)
    X, Z = np.meshgrid(c, c)           # fila = z, columna = x
    return X, Z


def leer_vertices(path, excluir_materiales=(), excluir_objetos=()):
    V, out, mat, obj = [], [], None, None
    with open(path, errors="ignore") as f:
        for l in f:
            if l.startswith("v "):
                V.append([float(x) for x in l.split()[1:4]])
            elif l.startswith("usemtl"):
                mat = l.split(None, 1)[1].strip()
            elif l.startswith("o "):
                obj = l.split(None, 1)[1].strip()
            elif l.startswith("f ") and mat not in excluir_materiales and not any(
                    obj and obj.startswith(p) for p in excluir_objetos):
                out += [V[int(p.split("/")[0]) - 1] for p in l.split()[1:]]
    return np.array(out, np.float32)


def distancia_a_polilinea(X, Z, pts):
    d = np.full(X.shape, 1e9, np.float32)
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        dx, dz = x1 - x0, z1 - z0
        t = np.clip(((X - x0) * dx + (Z - z0) * dz) / (dx * dx + dz * dz), 0, 1)
        d = np.minimum(d, np.hypot(X - (x0 + t * dx), Z - (z0 + t * dz)))
    return d


def en_rect(X, Z, r, margen=0.0):
    x0, x1, z0, z1 = r
    return (X >= x0 - margen) & (X <= x1 + margen) & (Z >= z0 - margen) & (Z <= z1 + margen)


# ------------------------------------------------------------------ Campos del mapa
def campos(res):
    """Calcula alturas y máscaras a la resolución indicada."""
    X, Z = coords(res)
    px = 2 * EXTENSION / (res - 1)

    # Ocupación de los objetos existentes (casa, cercas, corrales, caballos...)
    ocup = np.zeros((res, res), np.float32)
    for pts in OBJETOS:
        ix = np.clip(np.round((pts[:, 0] + EXTENSION) / px).astype(int), 0, res - 1)
        iz = np.clip(np.round((pts[:, 2] + EXTENSION) / px).astype(int), 0, res - 1)
        ocup[iz, ix] = 1.0
    for r in EXPLANADAS:
        ocup[en_rect(X, Z, r)] = 1.0
    d_caminos = np.min([distancia_a_polilinea(X, Z, c) for c in CAMINOS], axis=0)
    ocup[d_caminos < ANCHO_CAMINO] = 1.0
    ocup[np.hypot(X, Z - 45) < 20] = 1.0                       # punto de inicio de la cámara

    # Máscara de "terreno libre": 0 junto a objetos, 1 lejos (transición de ~35 unidades)
    cerca = suavizar(ocup, 9.0 / px)
    libre = 1.0 - np.clip(cerca * 6.0, 0, 1)
    libre = smoothstep(0.0, 1.0, suavizar(libre, 6.0 / px))

    # Relieve
    ondas = (fbm(res, 4, 6, SEMILLA) - 0.5) * 5.0
    colinas = np.zeros_like(X)
    for cx, cz, alto, radio in COLINAS:
        colinas += alto * np.exp(-((X - cx) ** 2 + (Z - cz) ** 2) / (2 * (radio * 0.5) ** 2))
    colinas *= 0.75 + 0.5 * fbm(res, 3, 8, SEMILLA + 7)
    r_caja = (np.abs(X) ** 4 + np.abs(Z) ** 4) ** 0.25
    sierra = smoothstep(235, 330, r_caja) * (16 + 26 * fbm(res, 4, 5, SEMILLA + 13)) \
        + smoothstep(330, 420, r_caja) * 12
    altura = NIVEL_BASE + libre * (ondas + colinas) + sierra * np.maximum(libre, 0.6)

    return X, Z, altura.astype(np.float32), libre, d_caminos, r_caja


def pendiente(altura, px):
    gz, gx = np.gradient(altura, px)
    return np.hypot(gx, gz)


# ------------------------------------------------------------------ Generación
def main():
    os.makedirs(SALIDA, exist_ok=True)
    global OBJETOS
    print("Leyendo modelos existentes...")
    OBJETOS = [
        leer_vertices(os.path.join(MODELOS, "Hacienda", "Hacienda.obj"), excluir_materiales=("Tereno",)),
        leer_vertices(os.path.join(MODELOS, "Caballos", "Horse.obj")),
        leer_vertices(os.path.join(MODELOS, "Mesas", "Mesas.obj")),
    ]
    OBJETOS = [o[o[:, 1] < 4.0] for o in OBJETOS]   # solo lo que toca el suelo

    # ---------------- Alturas (malla)
    n = int(round(2 * EXTENSION / PASO_MALLA)) + 1
    print(f"Alturas {n}x{n}...")
    _, _, altura, _, _, _ = campos(n)
    np.save(os.path.join(SALIDA, "altura.npy"), altura)

    # ---------------- Color del suelo
    res = RES_COLOR
    print(f"Textura de color {res}x{res}...")
    X, Z, alt, libre, d_caminos, r_caja = campos(res)
    px = 2 * EXTENSION / (res - 1)
    pend = pendiente(alt, px)

    n1 = fbm(res, 5, 24, SEMILLA + 21)
    n2 = fbm(res, 4, 60, SEMILLA + 22)
    n3 = fbm(res, 3, 70, SEMILLA + 23)
    bosque = fbm(res, 3, 7, SEMILLA + 31)

    verde = np.array([0.40, 0.55, 0.20])
    verde_osc = np.array([0.30, 0.45, 0.16])
    amarillo = np.array([0.62, 0.60, 0.30])
    tierra_osc = np.array([0.30, 0.26, 0.20])
    tierra = np.array([0.56, 0.45, 0.32])
    arcilla = np.array([0.68, 0.38, 0.25])
    hojarasca = np.array([0.36, 0.34, 0.18])

    t = smoothstep(0.35, 0.75, n1)[..., None]
    col = verde_osc * (1 - t) + verde * t
    seco = (smoothstep(0.58, 0.76, n2) * 0.65 + smoothstep(0.04, 0.14, pend) * 0.5)[..., None]
    col = col * (1 - np.clip(seco, 0, 1)) + amarillo * np.clip(seco, 0, 1)
    pasto = np.ones((res, res), np.float32)

    # Manchas de tierra oscura en el pasto (como en el jardín de la foto)
    manchas = smoothstep(0.70, 0.78, n3) * 0.6
    col = col * (1 - manchas[..., None]) + tierra_osc * manchas[..., None]
    pasto -= manchas * 0.8

    # Suelo de bosque (hojarasca) donde habrá árboles densos
    densidad = densidad_bosque(X, Z, bosque, libre, r_caja)
    h = (smoothstep(0.3, 0.8, densidad) * 0.7)[..., None]
    col = col * (1 - h) + hojarasca * h

    # Caminos de tierra con bordes irregulares
    borde = ANCHO_CAMINO * (0.75 + 0.5 * n2)
    c = 1 - smoothstep(borde * 0.55, borde, d_caminos)
    col = col * (1 - c[..., None]) + (tierra * (0.9 + 0.2 * n1[..., None])) * c[..., None]
    pasto -= c * 0.9

    # Explanadas de tierra roja (bordes suaves y algo irregulares)
    for r in EXPLANADAS:
        x0, x1, z0, z1 = r
        dx = np.maximum(np.maximum(x0 - X, X - x1), 0)
        dz = np.maximum(np.maximum(z0 - Z, Z - z1), 0)
        d = np.hypot(dx, dz) - (n2 - 0.5) * 4
        a = (1 - smoothstep(0.0, 2.5, d))
        tono = arcilla * (0.88 + 0.24 * n1[..., None]) * (1 - 0.15 * smoothstep(0.6, 0.8, n3)[..., None])
        col = col * (1 - a[..., None]) + tono * a[..., None]
        pasto -= a

    col = np.clip(col, 0, 1)
    pasto = np.clip(pasto, 0, 1)
    rgba = np.dstack([col * 255, pasto * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(os.path.join(SALIDA, "terreno_color.png"), optimize=True)

    # ---------------- Textura de detalle (repetible)
    print("Textura de detalle...")
    generar_detalle()

    # ---------------- Vegetación
    print("Vegetación...")
    vegetacion = generar_vegetacion(n, altura)
    with open(os.path.join(SALIDA, "vegetacion.json"), "w") as f:
        json.dump(vegetacion, f, separators=(",", ":"))
    print(f"  árboles: {len(vegetacion['arboles'])}, arbustos: {len(vegetacion['arbustos'])}")

    # ---------------- Colisión sin el terreno viejo
    print("Malla de colisión...")
    filtrar_colision()
    print("Listo.")


def densidad_bosque(X, Z, ruido_bosque, libre, r_caja):
    """0 = campo abierto, 1 = bosque denso."""
    d_casa = np.hypot(X - 30, Z + 20)
    interior = smoothstep(0.44, 0.60, ruido_bosque) * smoothstep(85, 150, d_casa)
    anillo = smoothstep(240, 270, r_caja)
    return np.clip(np.maximum(interior, anillo) * smoothstep(0.3, 0.8, libre), 0, 1)


def generar_detalle(res=512):
    """R: detalle de pasto (hojas finas), G: detalle de tierra (granos). Media ~128."""
    def tileable(celdas, semilla):
        r = np.random.default_rng(semilla)
        base = r.random((celdas, celdas)).astype(np.float32)
        base = np.tile(base, (3, 3))
        img = Image.fromarray(base).resize((res * 3, res * 3), Image.BICUBIC)
        return np.asarray(img)[res:2 * res, res:2 * res]

    pasto = 0.45 * tileable(128, 1) + 0.35 * tileable(256, 2) + 0.2 * tileable(32, 3)
    # Trazos verticales cortos (hojas de pasto)
    r = np.random.default_rng(4)
    trazos = np.zeros((res, res), np.float32)
    for _ in range(9000):
        x, y = r.integers(0, res, 2)
        largo = r.integers(3, 9)
        v = r.uniform(-0.5, 0.5)
        for k in range(largo):
            trazos[(y + k) % res, (x + int(k * r.uniform(-0.3, 0.3))) % res] += v
    pasto = pasto + 0.35 * trazos
    tierra = 0.5 * tileable(256, 5) + 0.3 * tileable(64, 6) + 0.2 * tileable(16, 7)
    granos = (r.random((res, res)) > 0.985).astype(np.float32) * r.uniform(-0.6, 0.6, (res, res))
    tierra = tierra + granos

    def normalizar(a, contraste):
        a = (a - a.mean()) / (a.std() + 1e-6)
        return np.clip(128 + a * contraste, 0, 255)

    img = np.dstack([normalizar(pasto, 30), normalizar(tierra, 22), np.full((res, res), 128)]).astype(np.uint8)
    Image.fromarray(img, "RGB").save(os.path.join(SALIDA, "terreno_detalle.png"), optimize=True)


def altura_en(altura, x, z):
    n = altura.shape[0]
    fx = (x + EXTENSION) / (2 * EXTENSION) * (n - 1)
    fz = (z + EXTENSION) / (2 * EXTENSION) * (n - 1)
    i0, j0 = int(np.clip(math.floor(fx), 0, n - 2)), int(np.clip(math.floor(fz), 0, n - 2))
    tx, tz = fx - i0, fz - j0
    a = altura[j0, i0] * (1 - tx) + altura[j0, i0 + 1] * tx
    b = altura[j0 + 1, i0] * (1 - tx) + altura[j0 + 1, i0 + 1] * tx
    return float(a * (1 - tz) + b * tz)


def generar_vegetacion(n, altura):
    res = 840
    X, Z, _, libre, d_caminos, r_caja = campos(res)
    bosque = fbm(res, 3, 7, SEMILLA + 31)
    dens = densidad_bosque(X, Z, bosque, libre, r_caja)
    px = 2 * EXTENSION / (res - 1)

    def muestra(campo, x, z):
        i = int(np.clip(round((x + EXTENSION) / px), 0, res - 1))
        j = int(np.clip(round((z + EXTENSION) / px), 0, res - 1))
        return float(campo[j, i])

    r = np.random.default_rng(SEMILLA + 99)
    arboles, ocupados = [], []
    celda = 7.0

    def lejos_de_otros(x, z, dmin):
        for ox, oz, od in ocupados[-400:]:
            if (x - ox) ** 2 + (z - oz) ** 2 < max(dmin, od) ** 2:
                return False
        return True

    # Árboles conservados de la versión anterior
    for x, z in ARBOLES_FIJOS:
        arboles.append(["guanacaste", int(r.integers(0, 4)), round(x, 2), round(altura_en(altura, x, z) - 0.2, 2),
                        round(z, 2), int(r.integers(0, 360)), round(float(r.uniform(1.0, 1.15)), 2)])
        ocupados.append((x, z, 10.0))

    coords_x = np.arange(-EXTENSION + celda / 2, EXTENSION, celda)
    for cz in coords_x:
        for cx in coords_x:
            x = cx + r.uniform(-celda * 0.45, celda * 0.45)
            z = cz + r.uniform(-celda * 0.45, celda * 0.45)
            lib = muestra(libre, x, z)
            if lib < 0.55 or muestra(d_caminos, x, z) < 7 or math.hypot(x - 30, z + 5) < 70:
                continue
            rc = (abs(x) ** 4 + abs(z) ** 4) ** 0.25
            d = muestra(dens, x, z)
            lejano = rc > 262
            if lejano:
                prob = 0.22 * d
            else:
                prob = 0.6 * d + 0.03             # bosque + árboles sueltos en el campo
            if r.random() > prob:
                continue
            dmin = 6.5 if d > 0.5 else 16.0
            if not lejos_de_otros(x, z, dmin):
                continue
            if lejano:
                tipo = "lejano"
            elif d < 0.4:
                tipo = r.choice(["guanacaste", "acacia", "guanacaste", "joven"])
            else:
                tipo = r.choice(["guanacaste", "acacia", "redondo", "joven", "redondo"])
            y = altura_en(altura, x, z) - 0.25
            arboles.append([str(tipo), int(r.integers(0, 4)), round(float(x), 2), round(y, 2), round(float(z), 2),
                            int(r.integers(0, 360)), round(float(r.uniform(0.8, 1.25)), 2)])
            ocupados.append((x, z, dmin))

    # Arbustos sueltos y en los bordes del bosque
    arbustos = []
    for _ in range(9000):
        x, z = r.uniform(-245, 245, 2)
        lib = muestra(libre, x, z)
        d = muestra(dens, x, z)
        if lib < 0.4 or muestra(d_caminos, x, z) < 5 or math.hypot(x - 30, z + 5) < 55:
            continue
        prob = 0.04 + 0.5 * d * (1 - d) * 4 * 0.3
        if r.random() > prob:
            continue
        arbustos.append([int(r.integers(0, 4)), round(float(x), 2), round(altura_en(altura, x, z) - 0.1, 2),
                         round(float(z), 2), int(r.integers(0, 360)), round(float(r.uniform(0.7, 1.4)), 2)])
    return {"arboles": arboles, "arbustos": arbustos}


def filtrar_colision():
    """Quita de colision_combined.obj los triángulos del terreno viejo (ahora el suelo
    nuevo se maneja con la grilla de alturas)."""
    V, cur, tris = [], None, []
    with open(os.path.join(MODELOS, "Hacienda", "Hacienda.obj"), errors="ignore") as f:
        for l in f:
            if l.startswith("v "):
                V.append([float(x) for x in l.split()[1:4]])
            elif l.startswith("usemtl"):
                cur = l.split()[1]
            elif l.startswith("f ") and cur == "Tereno":
                idx = [int(p.split("/")[0]) - 1 for p in l.split()[1:]]
                for k in range(1, len(idx) - 1):
                    tris.append([V[idx[0]], V[idx[k]], V[idx[k + 1]]])
    x0, z0, N = -345, -265, 640
    H = np.full((N, N), -1e9)
    xs, zs = np.arange(N) + x0, np.arange(N) + z0
    for A, B, C in tris:
        mnx, mxx = int(np.floor(min(A[0], B[0], C[0]))) - x0, int(np.ceil(max(A[0], B[0], C[0]))) - x0
        mnz, mxz = int(np.floor(min(A[2], B[2], C[2]))) - z0, int(np.ceil(max(A[2], B[2], C[2]))) - z0
        mnx, mnz, mxx, mxz = max(mnx, 0), max(mnz, 0), min(mxx, N - 1), min(mxz, N - 1)
        if mxx < mnx or mxz < mnz:
            continue
        gx, gz = np.meshgrid(xs[mnx:mxx + 1], zs[mnz:mxz + 1], indexing="ij")
        v0 = np.array([C[0] - A[0], C[2] - A[2]])
        v1 = np.array([B[0] - A[0], B[2] - A[2]])
        pxx, pzz = gx - A[0], gz - A[2]
        d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-12:
            continue
        d02, d12 = pxx * v0[0] + pzz * v0[1], pxx * v1[0] + pzz * v1[1]
        u, w = (d11 * d02 - d01 * d12) / den, (d00 * d12 - d01 * d02) / den
        m = (u >= -1e-3) & (w >= -1e-3) & (u + w <= 1 + 1e-3)
        y = A[1] + u * (C[1] - A[1]) + w * (B[1] - A[1])
        sub = H[mnx:mxx + 1, mnz:mxz + 1]
        sub[m] = np.maximum(sub[m], y[m])

    CV, F = [], []
    with open(os.path.join(MODELOS, "colision_combined.obj")) as f:
        for l in f:
            if l.startswith("v "):
                CV.append([float(x) for x in l.split()[1:4]])
            elif l.startswith("f "):
                F.append([int(p.split("/")[0]) - 1 for p in l.split()[1:]])
    CV, F = np.array(CV), np.array(F)
    i = np.clip(np.round(CV[:, 0] - x0).astype(int), 0, N - 1)
    j = np.clip(np.round(CV[:, 2] - z0).astype(int), 0, N - 1)
    suelo = (np.abs(CV[:, 1] - H[i, j]) < 0.45)[F].all(1)
    K = F[~suelo]
    usados = np.unique(K)
    remap = -np.ones(len(CV), int)
    remap[usados] = np.arange(len(usados))
    with open(os.path.join(MODELOS, "colision_hacienda.obj"), "w") as f:
        f.write("# Colisiones de la hacienda sin el terreno viejo (generado desde colision_combined.obj)\n")
        for p in CV[usados]:
            f.write("v %.5f %.5f %.5f\n" % tuple(p))
        for t in remap[K]:
            f.write("f %d %d %d\n" % tuple(t + 1))
    print(f"  triángulos: {len(F)} -> {len(K)}")


if __name__ == "__main__":
    main()
