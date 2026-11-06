# colisiones del jugador con la casa, los muebles, los caballos y las cercas
# el jugador es como una capsula: dos esferas (cabeza y cuerpo) que se empujan fuera de los
# triangulos, asi al chocar con una pared se resbala a lo largo de ella en vez de quedarse pegado
import math
from collections import defaultdict

import numpy as np

RADIO = 0.45                 # grosor del jugador
ESFERAS = (0.0, -0.9)        # alturas de las esferas respecto a la camara (cabeza y pecho)
PASO_MAX = RADIO * 0.5       # movimientos largos se parten en pasos cortos para no atravesar paredes


def leer_triangulos(ruta):
    V, T = [], []
    with open(ruta, encoding="utf-8", errors="ignore") as f:
        for l in f:
            if l.startswith("v "):
                V.append([float(x) for x in l.split()[1:4]])
            elif l.startswith("f "):
                idx = []
                for p in l.split()[1:]:
                    i = int(p.split("/")[0])
                    idx.append(i - 1 if i > 0 else len(V) + i)
                for k in range(1, len(idx) - 1):
                    T.append((idx[0], idx[k], idx[k + 1]))
    if not T:
        return np.zeros((0, 3, 3), np.float32)
    return np.asarray(V, np.float32)[np.asarray(T)]


def punto_mas_cercano(p, a, b, c):
    # punto de cada triangulo mas cercano a p (Ericson, Real-Time Collision Detection), con numpy
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp, cp = p - b, p - c
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    vc, vb, va = d1 * d4 - d3 * d2, d5 * d2 - d1 * d6, d3 * d6 - d5 * d4
    with np.errstate(divide="ignore", invalid="ignore"):
        den = 1.0 / (va + vb + vc)
        cara = a + ab * (vb * den)[:, None] + ac * (vc * den)[:, None]
        e_ab = a + ab * (d1 / (d1 - d3))[:, None]
        e_ac = a + ac * (d2 / (d2 - d6))[:, None]
        e_bc = b + (c - b) * ((d4 - d3) / ((d4 - d3) + (d5 - d6)))[:, None]
    condiciones = [(d1 <= 0) & (d2 <= 0), (d3 >= 0) & (d4 <= d3), (vc <= 0) & (d1 >= 0) & (d3 <= 0),
                   (d6 >= 0) & (d5 <= d6), (vb <= 0) & (d2 >= 0) & (d6 <= 0),
                   (va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0)]
    opciones = [a, b, e_ab, c, e_ac, e_bc]
    res = cara.copy()
    for cond, op in zip(reversed(condiciones), reversed(opciones)):   # la primera condicion gana
        res[cond] = op[cond]
    return np.nan_to_num(res, nan=1e9)


class MallaColision:
    # triangulos repartidos en una grilla (x, z) para revisar solo los cercanos

    def __init__(self, triangulos, celda=4.0):
        self.celda = celda
        self.tris = np.asarray(triangulos, np.float32)
        n = self.tris[:, 1] - self.tris[:, 0]
        n = np.cross(n, self.tris[:, 2] - self.tris[:, 0])
        largo = np.linalg.norm(n, axis=1)
        ok = largo > 1e-8
        self.tris = self.tris[ok]
        self.normales = n[ok] / largo[ok, None]
        celdas = defaultdict(list)
        lo = np.floor(self.tris.min(1)[:, [0, 2]] / celda).astype(int)
        hi = np.floor(self.tris.max(1)[:, [0, 2]] / celda).astype(int)
        for i, (l, h) in enumerate(zip(lo, hi)):
            for cx in range(l[0], h[0] + 1):
                for cz in range(l[1], h[1] + 1):
                    celdas[(cx, cz)].append(i)
        self.celdas = {k: np.array(v, np.int32) for k, v in celdas.items()}

    @classmethod
    def desde_obj(cls, *rutas):
        partes = [leer_triangulos(r) for r in rutas]
        return cls(np.concatenate([p for p in partes if len(p)]))

    def _cercanos(self, p, r):
        c = self.celda
        x0, x1 = int(math.floor((p[0] - r) / c)), int(math.floor((p[0] + r) / c))
        z0, z1 = int(math.floor((p[2] - r) / c)), int(math.floor((p[2] + r) / c))
        ids = [self.celdas[(cx, cz)] for cx in range(x0, x1 + 1) for cz in range(z0, z1 + 1) if (cx, cz) in self.celdas]
        if not ids:
            return None
        return np.unique(np.concatenate(ids)) if len(ids) > 1 else ids[0]

    def empuje(self, p, r):
        # vector para sacar la esfera (centro p, radio r) de los triangulos, o None si no toca nada
        ids = self._cercanos(p, r)
        if ids is None:
            return None
        t = self.tris[ids]
        p = np.asarray(p, np.float32)
        q = punto_mas_cercano(p, t[:, 0], t[:, 1], t[:, 2])
        d = p - q
        dist = np.linalg.norm(d, axis=1)
        toca = dist < r
        if not toca.any():
            return None
        d, dist, n = d[toca], dist[toca], self.normales[ids][toca]
        # direccion de salida: desde el punto mas cercano; si esta justo encima, la normal del triangulo
        dirs = np.where(dist[:, None] > 1e-5, d / np.maximum(dist, 1e-9)[:, None], n)
        k = int(np.argmin(dist))                  # primero el triangulo mas metido
        return dirs[k] * (r - dist[k] + 1e-3)


class Mundo:
    # junta la malla con los obstaculos simples (troncos, pedestales, vitrinas, borde del mapa)

    def __init__(self, malla, obstaculos=(), limite=None):
        self.malla = malla
        self.obstaculos = list(obstaculos)       # objetos con un metodo empuje(p, r)
        self.limite = limite

    def _empujar(self, p):
        for h in ESFERAS:
            q = p + np.array([0.0, h, 0.0])
            for _ in range(4):
                e = self.malla.empuje(q, RADIO)
                if e is None:
                    for o in self.obstaculos:
                        e = o.empuje(q, RADIO)
                        if e is not None:
                            break
                if e is None:
                    break
                q = q + e
            p = q - np.array([0.0, h, 0.0])
        return p

    def chocando(self, p):
        p = np.asarray(p, float)
        for h in ESFERAS:
            q = p + np.array([0.0, h, 0.0])
            if self.malla.empuje(q, RADIO * 0.9) is not None:
                return True
            if any(o.empuje(q, RADIO * 0.9) is not None for o in self.obstaculos):
                return True
        return False

    def mover(self, desde, hasta):
        # devuelve la posicion final: se resbala por las paredes y nunca las atraviesa
        a = np.asarray(desde, float)
        b = np.asarray(hasta, float)
        delta = b - a
        atrapado = self.chocando(a)              # si ya empezo adentro de algo, se le deja salir
        pasos = max(1, int(math.ceil(np.linalg.norm(delta) / PASO_MAX)))
        p = a.copy()
        for _ in range(pasos):
            nuevo = self._empujar(p + delta / pasos)
            if not atrapado and self.chocando(nuevo):
                break                            # esquina sin salida: se queda donde estaba
            p = nuevo
        if self.limite is not None:
            p = np.clip(p, -self.limite, self.limite)
        return [float(p[0]), float(p[1]), float(p[2])]
