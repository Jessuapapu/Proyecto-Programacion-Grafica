"""
Bosque: dibuja muchas copias de un mismo árbol (instancias) en distintas
posiciones, rotaciones y tamaños. El modelo se carga una sola vez en la GPU,
así que agregar árboles casi no cuesta memoria.
"""
from OpenGL.GL import *


class Arboles:
    def __init__(self, modelo, posiciones, radio_tronco=0.9, altura=13.5, distancia_max=420.0):
        """
        modelo      : Modelo.Modelos con un solo árbol cuya base del tronco está en el origen.
        posiciones  : lista de (x, y, z, rotacion_grados, escala).
        radio_tronco: radio de colisión del tronco (antes de escalar).
        altura      : altura aproximada del árbol (antes de escalar), para la colisión.
        """
        self.modelo = modelo
        self.posiciones = list(posiciones)
        self.radio_tronco = radio_tronco
        self.altura = altura
        self.distancia_max = distancia_max
        self.camara = None          # posición de la cámara, para no dibujar árboles muy lejanos

    # Misma interfaz que Modelo.Modelos, para poder usarlo dentro de Escenas
    def cargarmodelos(self):
        self.modelo.cargarmodelos()

    def liberar(self):
        self.modelo.liberar()

    def collides(self, punto):
        x, y, z = punto
        for ax, ay, az, _, esc in self.posiciones:
            r = self.radio_tronco * esc
            if (x - ax) ** 2 + (z - az) ** 2 < r * r and ay - 1.0 <= y <= ay + self.altura * esc:
                return True
        return False

    def draw(self):
        lim2 = self.distancia_max ** 2
        for x, y, z, rot, esc in self.posiciones:
            if self.camara is not None:
                dx, dz = x - self.camara[0], z - self.camara[2]
                if dx * dx + dz * dz > lim2:
                    continue
            glPushMatrix()
            glTranslatef(x, y, z)
            glRotatef(rot, 0.0, 1.0, 0.0)
            glScalef(esc, esc, esc)
            self.modelo.draw()
            glPopMatrix()
