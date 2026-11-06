"""
Árboles low-poly generados por código.

Cada función crea un árbol con la base del tronco en el origen y devuelve un
diccionario  material -> triángulos (array N x 3 x 3). Las copas se arman con
"gotas" (icosferas deformadas) para conservar el estilo low-poly facetado.

Tipos inspirados en el bosque seco de San Jacinto:
  guanacaste : copa ancha y aplanada en forma de sombrilla, tronco gris corto.
  acacia     : tronco delgado y torcido con la copa en pisos planos.
  redondo    : árbol frondoso de copa redonda y oscura (tipo mango / genízaro).
  joven      : árbol delgado y pequeño.
  lejano     : versión de pocos polígonos para el bosque del horizonte.
  arbusto    : matorral bajo.
"""
import math
import numpy as np

# Colores (Kd) de cada material
MATERIALES = {
    "Tronco":     (0.42, 0.33, 0.26),
    "TroncoGris": (0.58, 0.54, 0.47),
    "Hoja1":      (0.17, 0.34, 0.11),
    "Hoja2":      (0.22, 0.40, 0.14),
    "Hoja3":      (0.31, 0.48, 0.17),
    "HojaSeca":   (0.46, 0.49, 0.21),
}

# Radio del tronco (para las colisiones) de cada tipo, a escala 1
RADIO_TRONCO = {"guanacaste": 1.2, "acacia": 0.75, "redondo": 1.4, "joven": 0.5, "lejano": 1.1, "arbusto": 0.0}


# ------------------------------------------------------------------ Primitivas
def _icosaedro():
    t = (1 + 5 ** 0.5) / 2
    v = np.array([(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
                  (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)], np.float64)
    f = np.array([(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2),
                  (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5),
                  (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)])
    return v / np.linalg.norm(v, axis=1)[:, None], f


def _subdividir(v, f):
    v = list(map(tuple, v))
    cache, caras = {}, []

    def medio(a, b):
        k = (min(a, b), max(a, b))
        if k not in cache:
            p = (np.array(v[a]) + np.array(v[b])) / 2
            v.append(tuple(p / np.linalg.norm(p)))
            cache[k] = len(v) - 1
        return cache[k]

    for a, b, c in f:
        ab, bc, ca = medio(a, b), medio(b, c), medio(c, a)
        caras += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
    return np.array(v), np.array(caras)


_V0, _F0 = _icosaedro()
_V1, _F1 = _subdividir(_V0, _F0)
_ESFERAS = {0: (_V0, _F0), 1: (_V1, _F1)}


def gota(centro, radios, detalle, rng, irregular=0.2, aplastar_base=0.35):
    """Icosfera deformada: base algo aplanada y vértices desplazados al azar."""
    v, f = _ESFERAS[detalle]
    v = v * (1 + rng.uniform(-irregular, irregular, (len(v), 1)))
    v = v.copy()
    abajo = v[:, 1] < 0
    v[abajo, 1] *= (1 - aplastar_base)
    v = v * np.asarray(radios) + np.asarray(centro)
    return v[f]


def cilindro(p0, p1, r0, r1, lados, rng=None, giro=0.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    eje = p1 - p0
    eje_n = eje / (np.linalg.norm(eje) + 1e-9)
    aux = np.array([1.0, 0, 0]) if abs(eje_n[0]) < 0.9 else np.array([0, 0, 1.0])
    u = np.cross(eje_n, aux)
    u /= np.linalg.norm(u)
    w = np.cross(eje_n, u)
    ang = np.linspace(0, 2 * math.pi, lados, endpoint=False) + giro
    dirs = np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * w
    a = p0 + dirs * r0
    b = p1 + dirs * r1
    tris = []
    for i in range(lados):
        j = (i + 1) % lados
        tris.append([a[i], a[j], b[j]])
        tris.append([a[i], b[j], b[i]])
    return np.array(tris)


class _Arbol:
    def __init__(self):
        self.partes = {}

    def agregar(self, material, tris):
        self.partes.setdefault(material, []).append(np.asarray(tris, np.float64))

    def resultado(self):
        return {m: np.concatenate(t) for m, t in self.partes.items()}


def _hoja(rng, opciones):
    return opciones[int(rng.integers(0, len(opciones)))]


# ------------------------------------------------------------------ Tipos de árbol
def guanacaste(rng):
    a = _Arbol()
    alto = rng.uniform(7.0, 9.0)
    tope = np.array([rng.uniform(-0.6, 0.6), alto, rng.uniform(-0.6, 0.6)])
    a.agregar("TroncoGris", cilindro((0, -0.5, 0), tope, 1.15, 0.85, 7, giro=rng.uniform(0, 6)))
    copa_y = alto + rng.uniform(9.0, 11.0)
    n = int(rng.integers(3, 5))
    base_ang = rng.uniform(0, 2 * math.pi)
    for i in range(n):
        ang = base_ang + i * 2 * math.pi / n + rng.uniform(-0.3, 0.3)
        r = rng.uniform(7.0, 10.0)
        medio = tope + np.array([math.cos(ang) * r * 0.45, (copa_y - alto) * 0.5, math.sin(ang) * r * 0.45])
        fin = np.array([math.cos(ang) * r, copa_y - rng.uniform(0.5, 1.5), math.sin(ang) * r])
        a.agregar("TroncoGris", cilindro(tope, medio, 0.7, 0.45, 5))
        a.agregar("TroncoGris", cilindro(medio, fin, 0.45, 0.25, 5))
        a.agregar(_hoja(rng, ["Hoja1", "Hoja2", "Hoja2"]),
                  gota(fin + (0, 1.4, 0), (rng.uniform(6.5, 8.0), rng.uniform(2.4, 3.0), rng.uniform(6.5, 8.0)), 1, rng))
    # Copa central ancha y plana (la "sombrilla")
    a.agregar(_hoja(rng, ["Hoja2", "Hoja3"]), gota((0, copa_y + 2.2, 0), (9.5, 2.6, 9.5), 1, rng, 0.15))
    for _ in range(4):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(7, 11)
        a.agregar(_hoja(rng, ["Hoja2", "Hoja3"]),
                  gota((math.cos(ang) * r, copa_y + rng.uniform(1.5, 3.5), math.sin(ang) * r),
                       (rng.uniform(3, 4.5), rng.uniform(1.3, 1.8), rng.uniform(3, 4.5)), 0, rng))
    return a.resultado()


def acacia(rng):
    a = _Arbol()
    p0 = np.array([0.0, -0.5, 0.0])
    p1 = np.array([rng.uniform(-1.5, 1.5), rng.uniform(7, 9), rng.uniform(-1.5, 1.5)])
    p2 = p1 + np.array([rng.uniform(-2.5, 2.5), rng.uniform(5, 7), rng.uniform(-2.5, 2.5)])
    a.agregar("Tronco", cilindro(p0, p1, 0.72, 0.52, 6))
    a.agregar("Tronco", cilindro(p1, p2, 0.52, 0.36, 6))
    pisos = int(rng.integers(2, 4))
    for i in range(pisos):
        t = i / max(1, pisos - 1)
        y = p2[1] + 1.5 + i * rng.uniform(2.6, 3.4)
        radio = 9.0 - 2.6 * i + rng.uniform(-1, 1)
        centro = np.array([p2[0] + rng.uniform(-2.5, 2.5), y, p2[2] + rng.uniform(-2.5, 2.5)])
        rama_ini = p1 + (p2 - p1) * (0.4 + 0.6 * t)
        a.agregar("Tronco", cilindro(rama_ini, centro - (0, 0.8, 0), 0.4, 0.22, 5))
        a.agregar(_hoja(rng, ["Hoja2", "Hoja3", "HojaSeca"]),
                  gota(centro, (radio, rng.uniform(1.1, 1.5), radio * rng.uniform(0.8, 1.0)), 1, rng, 0.18, 0.6))
        for _ in range(2):
            ang, r = rng.uniform(0, 2 * math.pi), radio * rng.uniform(0.5, 0.8)
            a.agregar(_hoja(rng, ["Hoja2", "Hoja3"]),
                      gota(centro + (math.cos(ang) * r, 0.6, math.sin(ang) * r),
                           (radio * 0.35, 1.0, radio * 0.35), 0, rng))
    return a.resultado()


def redondo(rng):
    a = _Arbol()
    alto = rng.uniform(5.0, 6.5)
    tope = np.array([rng.uniform(-0.4, 0.4), alto, rng.uniform(-0.4, 0.4)])
    a.agregar("Tronco", cilindro((0, -0.5, 0), tope, 1.35, 1.0, 7))
    for i in range(3):
        ang = rng.uniform(0, 2 * math.pi)
        a.agregar("Tronco", cilindro(tope, tope + (math.cos(ang) * 3.5, 5.0, math.sin(ang) * 3.5), 0.6, 0.35, 5))
    centro = tope + np.array([0, 9.0, 0])
    a.agregar(_hoja(rng, ["Hoja1", "Hoja2"]), gota(centro, (8.5, 7.0, 8.5), 1, rng, 0.14, 0.3))
    for _ in range(int(rng.integers(4, 6))):
        ang = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(4.5, 6.5)
        c = centro + np.array([math.cos(ang) * r, rng.uniform(-2.5, 3.0), math.sin(ang) * r])
        s = rng.uniform(4.0, 5.5)
        a.agregar(_hoja(rng, ["Hoja1", "Hoja1", "Hoja2"]), gota(c, (s, s * 0.85, s), 1 if s > 4.8 else 0, rng))
    return a.resultado()


def joven(rng):
    a = _Arbol()
    alto = rng.uniform(9, 12)
    tope = np.array([rng.uniform(-1, 1), alto, rng.uniform(-1, 1)])
    a.agregar("Tronco", cilindro((0, -0.5, 0), tope, 0.45, 0.28, 5))
    for i in range(int(rng.integers(2, 4))):
        c = tope + np.array([rng.uniform(-2, 2), rng.uniform(1.5, 4.0) + i * 1.2, rng.uniform(-2, 2)])
        s = rng.uniform(3.0, 4.2)
        a.agregar(_hoja(rng, ["Hoja2", "Hoja3", "Hoja3"]), gota(c, (s, s * 0.8, s), 1 if i == 0 else 0, rng))
    return a.resultado()


def lejano(rng):
    a = _Arbol()
    alto = rng.uniform(7, 10)
    a.agregar("Tronco", cilindro((0, -0.5, 0), (0, alto, 0), 1.1, 0.75, 5))
    for i in range(int(rng.integers(2, 4))):
        ang = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0, 4.5)
        c = (math.cos(ang) * r, alto + rng.uniform(5, 9), math.sin(ang) * r)
        a.agregar(_hoja(rng, ["Hoja1", "Hoja2", "Hoja2", "Hoja3"]),
                  gota(c, (rng.uniform(7, 10), rng.uniform(3.5, 5.5), rng.uniform(7, 10)), 0, rng, 0.25))
    return a.resultado()


def arbusto(rng):
    a = _Arbol()
    for _ in range(int(rng.integers(4, 7))):
        ang, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 1.4)
        s = rng.uniform(0.6, 1.1)
        a.agregar(_hoja(rng, ["Hoja3", "Hoja3", "HojaSeca"]),
                  gota((math.cos(ang) * r, s * 0.5 + rng.uniform(0, 0.8), math.sin(ang) * r),
                       (s, s * 0.85, s), 0, rng, 0.3, 0.4))
    return a.resultado()


TIPOS = {"guanacaste": guanacaste, "acacia": acacia, "redondo": redondo,
         "joven": joven, "lejano": lejano, "arbusto": arbusto}


def prototipo(tipo, variante):
    """Árbol de un tipo y variante (cada variante es una forma distinta pero siempre la misma)."""
    semilla = sum(ord(c) for c in tipo) * 131 + int(variante) * 7919
    return TIPOS[tipo](np.random.default_rng(semilla))


def combinar(instancias, uv=(0.0, 0.0)):
    """Junta muchas copias de árboles en un solo bloque por material.
    instancias: lista de (tipo, variante, x, y, z, rotacion_grados, escala).
    Devuelve material -> array float32 (N, 8) con posición, uv y normal (sombreado facetado)."""
    grupos = {}
    for tipo, var, x, y, z, rot, esc in instancias:
        grupos.setdefault((tipo, int(var)), []).append((x, y, z, rot, esc))

    salida = {}
    for (tipo, var), lista in grupos.items():
        proto = prototipo(tipo, var)
        datos = np.array(lista, np.float64)
        ang = np.radians(datos[:, 3])
        c, s = np.cos(ang), np.sin(ang)
        # Matrices de rotación en Y para todas las instancias: (n, 3, 3)
        R = np.zeros((len(datos), 3, 3))
        R[:, 0, 0], R[:, 0, 2], R[:, 1, 1], R[:, 2, 0], R[:, 2, 2] = c, s, 1, -s, c
        for mat, tris in proto.items():
            n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
            n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
            # posiciones: (inst, tri, vert, 3)
            p = np.einsum("nij,tvj->ntvi", R, tris) * datos[:, 4, None, None, None] \
                + datos[:, None, None, 0:3]
            nn = np.einsum("nij,tj->nti", R, n)
            nn = np.repeat(nn[:, :, None, :], 3, axis=2)
            bloque = np.empty(p.shape[:3] + (8,), np.float32)
            bloque[..., 0:3] = p
            bloque[..., 3] = uv[0]
            bloque[..., 4] = uv[1]
            bloque[..., 5:8] = nn
            salida.setdefault(mat, []).append(bloque.reshape(-1, 8))
    return {m: np.concatenate(b) for m, b in salida.items()}
