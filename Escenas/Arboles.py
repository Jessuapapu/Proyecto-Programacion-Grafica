# bosque low poly, las posiciones vienen de vegetacion.json
# todos los arboles se juntan en un solo modelo para que no sea lento
import json
import math
from collections import defaultdict

from Clases.Modelo import Modelos
from Clases import ArbolesLowPoly
from Escenas import Iluminacion

# altura del tronco para colisiones, arriba de eso se puede pasar
ALTURA_TRONCO = 12.0
LIMITE_COLISION = 260.0     # solo arboles cerca del area donde se camina
CELDA = 10.0                # tamaño de celda para las colisiones


class Bosque:

    def __init__(self, ruta_json):
        self.ruta_json = ruta_json
        self.modelo = None
        self.cantidad = 0
        self._celdas = defaultdict(list)    # celda: troncos

    def cargarmodelos(self):
        with open(self.ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
        # tipo, variante, x, y, z, rotacion, escala
        arboles = [tuple(a) for a in datos.get("arboles", [])]
        arbustos = [("arbusto",) + tuple(a) for a in datos.get("arbustos", [])]
        self.cantidad = len(arboles)

        # juntar todo por material
        geometria = ArbolesLowPoly.combinar(arboles + arbustos)
        self.modelo = Modelos.desde_datos(geometria, ArbolesLowPoly.MATERIALES)
        self.modelo.modos = {m: Iluminacion.MODO_FOLLAJE for m in ArbolesLowPoly.MATERIALES if m.startswith("Hoja")}

        # guardar cada tronco en las celdas que toca
        for tipo, _, x, y, z, _, esc in arboles:
            radio = ArbolesLowPoly.RADIO_TRONCO.get(tipo, 0.0) * esc
            if radio <= 0 or abs(x) > LIMITE_COLISION or abs(z) > LIMITE_COLISION:
                continue
            tronco = (x, y, z, radio, ALTURA_TRONCO * esc)
            for cx in range(int(math.floor((x - radio) / CELDA)), int(math.floor((x + radio) / CELDA)) + 1):
                for cz in range(int(math.floor((z - radio) / CELDA)), int(math.floor((z + radio) / CELDA)) + 1):
                    self._celdas[(cx, cz)].append(tronco)

    def empuje(self, p, r):
        # empuja una esfera fuera de los troncos (solo en horizontal)
        x, y, z = p
        vistos = set()
        for cx in range(int(math.floor((x - r) / CELDA)), int(math.floor((x + r) / CELDA)) + 1):
            for cz in range(int(math.floor((z - r) / CELDA)), int(math.floor((z + r) / CELDA)) + 1):
                for t in self._celdas.get((cx, cz), ()):
                    if t in vistos:
                        continue
                    vistos.add(t)
                    ax, ay, az, radio, alto = t
                    if not (ay - 1.0 <= y <= ay + alto):
                        continue
                    dx, dz = x - ax, z - az
                    d = math.hypot(dx, dz)
                    falta = radio + r - d
                    if falta > 0:
                        if d < 1e-6:
                            dx, dz, d = 1.0, 0.0, 1.0
                        return (dx / d * falta, 0.0, dz / d * falta)
        return None

    def collides(self, punto):
        x, y, z = punto
        for ax, ay, az, radio, alto in self._celdas.get((int(math.floor(x / CELDA)), int(math.floor(z / CELDA))), ()):
            if (x - ax) ** 2 + (z - az) ** 2 < radio * radio and ay - 1.0 <= y <= ay + alto:
                return True
        return False

    def draw(self):
        if self.modelo is not None:
            self.modelo.draw()

    def liberar(self):
        if self.modelo is not None:
            self.modelo.liberar()
