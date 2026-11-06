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
