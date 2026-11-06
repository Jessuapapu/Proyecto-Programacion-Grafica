# vitrinas de armas del museo (como en las fotos)
# mueble dorado, terciopelo rojo, vidrio, revolveres, bayonetas y fusiles
import math
import numpy as np

from Clases import ArbolesLowPoly as LP

COLORES = {
    "Oro": (0.78, 0.60, 0.26),
    "Terciopelo": (0.58, 0.06, 0.08),
    "MetalArma": (0.20, 0.20, 0.21),
    "MetalOxido": (0.30, 0.26, 0.22),
    "MaderaArma": (0.36, 0.20, 0.10),
    "Cacha": (0.72, 0.58, 0.40),
    "Vidrio": (0.82, 0.92, 0.95),
}

ALTO_PATAS = 2.6        # altura del terciopelo
ALTO_VIDRIO = 3.2       # altura del vidrio


# figuras basicas
def _normalizar(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-12)


def hexaedro(p):
    # 8 esquinas (0-3 un lado, 4-7 el otro) a triangulos
    p = [np.asarray(v, float) for v in p]
    caras = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    tris = []
    for a, b, c, d in caras:
        tris.append([p[a], p[b], p[c]])
        tris.append([p[a], p[c], p[d]])
    return np.array(tris)


def barra(p0, p1, ancho, alto, arriba=(0, 1, 0), ancho1=None, alto1=None, desplazar=(0, 0)):
    # prisma de p0 a p1, puede ser mas delgado en p1
    ancho1 = ancho if ancho1 is None else ancho1
    alto1 = alto if alto1 is None else alto1
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = _normalizar(p1 - p0)
    lado = _normalizar(np.cross(d, arriba))
    up = np.cross(lado, d)
    def anillo(c, w, h, dz=0.0):
        # rectangulo w x h centrado en c
        c = c + up * dz
        return [c - lado * w / 2 - up * h / 2, c + lado * w / 2 - up * h / 2,
                c + lado * w / 2 + up * h / 2, c - lado * w / 2 + up * h / 2]
    return hexaedro(anillo(p0, ancho, alto, desplazar[0]) + anillo(p1, ancho1, alto1, desplazar[1]))


def caja(x0, x1, y0, y1, z0, z1):
    return barra((x0, (y0 + y1) / 2, (z0 + z1) / 2), (x1, (y0 + y1) / 2, (z0 + z1) / 2), z1 - z0, y1 - y0)


def cilindro(p0, p1, r0, r1=None, lados=10):
    return LP.cilindro(p0, p1, r0, r0 if r1 is None else r1, lados)


def tapa(centro, eje, r, lados=10):
    eje = _normalizar(eje)
    aux = np.array([1.0, 0, 0]) if abs(eje[0]) < 0.9 else np.array([0, 0, 1.0])
    u = _normalizar(np.cross(eje, aux))
    w = np.cross(eje, u)
    c = np.asarray(centro, float)
    tris = []
    for i in range(lados):
        a0, a1 = 2 * math.pi * i / lados, 2 * math.pi * (i + 1) / lados
        tris.append([c, c + (math.cos(a0) * u + math.sin(a0) * w) * r, c + (math.cos(a1) * u + math.sin(a1) * w) * r])
    return np.array(tris)


# armas
def revolver(rng):
    # revolver acostado, mide como 1 unidad
    p = {}
    t = 0.07                        # mitad del grosor
    y = t
    largo_canon = rng.uniform(0.42, 0.58)
    p.setdefault("MetalArma", []).append(cilindro((0.10, y, 0), (0.10 + largo_canon, y, 0), 0.032, lados=8))
    p["MetalArma"].append(barra((0.10, y, -0.035), (0.10 + largo_canon * 0.85, y, -0.035), 0.05, 0.03, arriba=(0, 0, 1)))  # baqueta
    p["MetalArma"].append(cilindro((-0.06, y, 0), (0.10, y, 0), 0.075, lados=8))           # tambor
    p["MetalArma"].append(barra((-0.20, y, -0.01), (0.12, y, -0.01), 0.13, 0.10, arriba=(0, 0, 1)))  # armazón
    p["MetalArma"].append(barra((-0.20, y, 0.05), (-0.29, y, 0.10), 0.03, 0.06, arriba=(0, 0, 1)))  # martillo
    p["MetalArma"].append(barra((-0.10, y, -0.07), (-0.02, y, -0.15), 0.02, 0.025, arriba=(0, 0, 1)))  # gatillo
    p["MetalArma"].append(barra((-0.14, y, -0.17), (0.02, y, -0.13), 0.015, 0.03, arriba=(0, 0, 1)))  # guardamonte
    cacha = "Cacha" if rng.random() < 0.5 else "MaderaArma"
    p.setdefault(cacha, []).append(barra((-0.18, y, -0.03), (-0.36, y, -0.30), 0.14, 0.11,
                                         arriba=(0, 1, 0), ancho1=0.12, alto1=0.12))
    return {k: np.concatenate(v) for k, v in p.items()}


def bayoneta(rng):
    # bayoneta de cubo acostada
    p = {"MetalOxido": []}
    y = 0.06
    p["MetalOxido"].append(cilindro((0, y, 0), (0.32, y, 0), 0.06, lados=8))
    p["MetalOxido"].append(tapa((0, y, 0), (-1, 0, 0), 0.06, 8))
    p["MetalOxido"].append(barra((0.30, y, 0), (0.36, y, 0.14), 0.05, 0.05))                  # codo
    largo = rng.uniform(1.6, 1.9)
    p["MetalOxido"].append(barra((0.36, 0.03, 0.14), (0.36 + largo, 0.02, 0.14), 0.10, 0.045,
                                 ancho1=0.012, alto1=0.012))
    return {k: np.concatenate(v) for k, v in p.items()}


def fusil(rng, largo=4.6):
    # fusil de avancarga de perfil
    p = {"MetalArma": [], "MaderaArma": []}
    x_culata, x_boca = -largo * 0.5, largo * 0.5
    x_cola = x_culata + largo * 0.24
    # culata
    p["MaderaArma"].append(barra((x_cola, 0.0, 0), (x_culata, -0.12, 0), 0.10, 0.16,
                                 ancho1=0.12, alto1=0.42, desplazar=(0, -0.05)))
    # guardamano
    p["MaderaArma"].append(barra((x_cola, 0.0, 0), (x_boca - 0.45, 0.02, 0), 0.10, 0.13, ancho1=0.08, alto1=0.09))
    # cañon y baqueta
    p["MetalArma"].append(cilindro((x_cola - 0.05, 0.085, 0), (x_boca, 0.085, 0), 0.045, 0.038, 10))
    p["MetalArma"].append(cilindro((x_cola + 0.4, -0.04, 0), (x_boca - 0.1, -0.04, 0), 0.014, lados=6))
    # abrazaderas
    for f in (0.45, 0.75):
        x = x_cola + (x_boca - x_cola) * f
        p["MetalArma"].append(cilindro((x - 0.04, 0.04, 0), (x + 0.04, 0.04, 0), 0.10, lados=10))
    # llave, martillo y gatillo
    p["MetalArma"].append(barra((x_cola - 0.02, 0.03, 0.055), (x_cola + 0.30, 0.03, 0.055), 0.02, 0.10))
    p["MetalArma"].append(barra((x_cola + 0.02, 0.09, 0.07), (x_cola - 0.06, 0.20, 0.07), 0.03, 0.04, arriba=(0, 0, 1)))
    p["MetalArma"].append(barra((x_cola + 0.12, -0.06, 0), (x_cola + 0.10, -0.16, 0), 0.02, 0.025, arriba=(0, 0, 1)))
    p["MetalArma"].append(barra((x_cola + 0.0, -0.18, 0), (x_cola + 0.28, -0.08, 0), 0.015, 0.025, arriba=(0, 0, 1)))
    # cantonera
    p["MetalArma"].append(barra((x_culata + 0.02, -0.12 - 0.05, 0), (x_culata - 0.01, -0.12 - 0.05, 0), 0.125, 0.44))
    return {k: np.concatenate(v) for k, v in p.items()}


# vitrina
def _mover(tris, R, t):
    return tris @ R.T + t


def construir(x, piso, z, rot, n_revolveres=6, n_bayonetas=3, n_fusiles=3, largo=6.0, fondo=2.2, semilla=0):
    # devuelve opacos, vidrio, tarjetas y caja de colision
    rng = np.random.default_rng(1856 + semilla)
    a = math.radians(rot)
    R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    T = np.array([x, piso, z])
    L2, F2 = largo / 2, fondo / 2
    yv = ALTO_PATAS
    yt = yv + ALTO_VIDRIO
    g = 0.07                         # grosor de los perfiles
    opacos = {}

    def add(mat, tris):
        opacos.setdefault(mat, []).append(_mover(np.asarray(tris), R, T))

    # patas
    for sx in (-1, 1):
        for sz in (-1, 1):
            add("Oro", caja(sx * L2 - g, sx * L2 + g, 0, yv, sz * F2 - g, sz * F2 + g))
    for yb in (0.55, yv - 0.15):
        for sz in (-1, 1):
            add("Oro", caja(-L2, L2, yb - g / 2, yb + g / 2, sz * F2 - g / 2, sz * F2 + g / 2))
        for sx in (-1, 1):
            add("Oro", caja(sx * L2 - g / 2, sx * L2 + g / 2, yb - g / 2, yb + g / 2, -F2, F2))
    # base y terciopelo
    add("Oro", caja(-L2 - 0.05, L2 + 0.05, yv - 0.12, yv, -F2 - 0.05, F2 + 0.05))
    add("Terciopelo", caja(-L2 + 0.02, L2 - 0.02, yv, yv + 0.03, -F2 + 0.02, F2 - 0.02))
    # perfiles del vidrio
    for sx in (-1, 1):
        for sz in (-1, 1):
            add("Oro", caja(sx * L2 - g / 2, sx * L2 + g / 2, yv, yt, sz * F2 - g / 2, sz * F2 + g / 2))
    for sz in (-1, 1):
        add("Oro", caja(-L2, L2, yt - g / 2, yt + g / 2, sz * F2 - g / 2, sz * F2 + g / 2))
    for sx in (-1, 1):
        add("Oro", caja(sx * L2 - g / 2, sx * L2 + g / 2, yt - g / 2, yt + g / 2, -F2, F2))
    add("Oro", caja(-g / 2, g / 2, yv, yt, F2 - g / 2, F2 + g / 2))

    # armas encima del terciopelo
    y0 = yv + 0.03
    zona_rev = largo * 0.58
    for i in range(n_revolveres):
        px = -L2 + 0.55 + (i + 0.5) * (zona_rev - 0.3) / max(1, n_revolveres)
        ang = math.radians(rng.uniform(55, 70))
        Rl = np.array([[math.cos(ang), 0, math.sin(ang)], [0, 1, 0], [-math.sin(ang), 0, math.cos(ang)]])
        for mat, tris in revolver(rng).items():
            add(mat, tris @ Rl.T + np.array([px, y0, 0.05]))
    for i in range(n_bayonetas):
        ang = math.radians(rng.uniform(-14, -8))
        Rl = np.array([[math.cos(ang), 0, math.sin(ang)], [0, 1, 0], [-math.sin(ang), 0, math.cos(ang)]])
        base = np.array([-L2 + zona_rev + 0.15, y0, -0.55 + i * 0.42])
        for mat, tris in bayoneta(rng).items():
            add(mat, tris @ Rl.T + base)

    # fusiles colgados con soportes
    for i in range(n_fusiles):
        yf = yv + 0.75 + i * 0.85
        dx = rng.uniform(-0.2, 0.2)
        for mat, tris in fusil(rng, largo * 0.8).items():
            add(mat, tris + np.array([dx, yf, -F2 + 0.45]))
        for sx in (-1, 1):
            xs = dx + sx * largo * 0.22
            add("Oro", caja(xs - 0.03, xs + 0.03, yf - 0.16, yf - 0.10, -F2, -F2 + 0.55))

    # vidrios
    vidrio = []
    for sz in (-1, 1):
        zz = sz * F2
        vidrio += [[(-L2, yv, zz), (L2, yv, zz), (L2, yt, zz)], [(-L2, yv, zz), (L2, yt, zz), (-L2, yt, zz)]]
    for sx in (-1, 1):
        xx = sx * L2
        vidrio += [[(xx, yv, -F2), (xx, yv, F2), (xx, yt, F2)], [(xx, yv, -F2), (xx, yt, F2), (xx, yt, -F2)]]
    vidrio += [[(-L2, yt, -F2), (L2, yt, -F2), (L2, yt, F2)], [(-L2, yt, -F2), (L2, yt, F2), (-L2, yt, F2)]]
    vidrio = _mover(np.array(vidrio, float), R, T)

    # fichas
    tarjetas = []
    def tarjeta(cx, cz, w, h, texto):
        # tarjeta con el nombre del arma
        inclin = 0.35
        p0 = np.array([cx - w / 2, y0 + 0.01, cz + h * math.cos(inclin) / 2])
        p1 = np.array([cx + w / 2, y0 + 0.01, cz + h * math.cos(inclin) / 2])
        p2 = np.array([cx + w / 2, y0 + 0.01 + h * math.sin(inclin), cz - h * math.cos(inclin) / 2])
        p3 = np.array([cx - w / 2, y0 + 0.01 + h * math.sin(inclin), cz - h * math.cos(inclin) / 2])
        esq = _mover(np.array([p0, p1, p2, p3]), R, T)
        tarjetas.append((esq, texto))
    tarjeta(-L2 + zona_rev * 0.55, F2 - 0.3, 0.9, 0.32, ["Revólveres de la época"])
    tarjeta(L2 - 0.75, F2 - 0.25, 0.7, 0.28, ["Bayonetas"])
    tarjeta(-L2 + 0.75, F2 - 0.3, 1.1, 0.42, ["Armas utilizadas en la", "época de la Batalla de", "San Jacinto (1856)"])

    # caja de colision
    esquinas = _mover(np.array([[-L2 - 0.3, 0, -F2 - 0.3], [L2 + 0.3, 0, F2 + 0.3],
                                [-L2 - 0.3, 0, F2 + 0.3], [L2 + 0.3, 0, -F2 - 0.3]]), R, T)
    colision = (esquinas[:, 0].min(), esquinas[:, 0].max(), esquinas[:, 2].min(), esquinas[:, 2].max(), piso + yt + 0.5)
    return {k: np.concatenate(v) for k, v in opacos.items()}, vidrio, tarjetas, colision
