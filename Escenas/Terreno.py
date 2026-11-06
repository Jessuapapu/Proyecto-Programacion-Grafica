"""
Terreno del mapa: malla de alturas con relieve (zona plana alrededor de la
hacienda, lomas suaves en el campo y una sierra boscosa en el horizonte).

Los datos salen de modelosObj/Terreno/ (ver Recursos/Herramientas/generar_mapa.py):
  altura.npy           alturas en una grilla regular
  terreno_color.png    color del suelo; el canal alfa indica cuánto pasto hay
  terreno_detalle.png  detalle fino repetible (pasto / tierra) que usa el shader
"""
import os
import numpy as np
from OpenGL.GL import *
from OpenGL.arrays import vbo

from Clases.Modelo import Modelos
from Escenas import Iluminacion

STRIDE = 8 * 4   # posición (3) + uv (2) + normal (3)


class Terreno:
    def __init__(self, carpeta, extension=420.0):
        self.carpeta = carpeta
        self.extension = extension
        self.altura = None
        self._vbo = None
        self._ibo = None
        self._n_indices = 0
        self.tex_color = None
        self.tex_detalle = None

    # Misma interfaz que Modelo.Modelos para poder usarlo dentro de Escenas
    def cargarmodelos(self):
        ruta = os.path.join(self.carpeta, "altura.npy")
        if not os.path.isfile(ruta):
            raise FileNotFoundError(f"No se encontró el terreno: {ruta}")
        self.altura = np.load(ruta).astype(np.float32)
        n = self.altura.shape[0]
        e = self.extension
        paso = 2 * e / (n - 1)

        c = np.linspace(-e, e, n, dtype=np.float32)
        X, Z = np.meshgrid(c, c)                     # fila = z, columna = x
        gz, gx = np.gradient(self.altura, paso)
        normales = np.dstack([-gx, np.ones_like(gx), -gz])
        normales /= np.linalg.norm(normales, axis=2, keepdims=True)

        datos = np.dstack([X, self.altura, Z, (X + e) / (2 * e), (Z + e) / (2 * e), normales])
        datos = np.ascontiguousarray(datos.reshape(-1, 8), dtype=np.float32)

        j, i = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing="ij")
        a = (j * n + i).ravel()
        b, cc = a + 1, a + n
        d = cc + 1
        indices = np.stack([a, cc, b, b, cc, d], axis=1).astype(np.uint32).ravel()

        self._vbo = vbo.VBO(datos)
        self._ibo = vbo.VBO(np.ascontiguousarray(indices), target=GL_ELEMENT_ARRAY_BUFFER)
        self._n_indices = len(indices)

        self.tex_color, _ = Modelos._cargar_textura(os.path.join(self.carpeta, "terreno_color.png"))
        self.tex_detalle, _ = Modelos._cargar_textura(os.path.join(self.carpeta, "terreno_detalle.png"))

    def altura_en(self, x, z):
        """Altura del suelo en (x, z) con interpolación bilineal."""
        if self.altura is None:
            return -1e9
        n = self.altura.shape[0]
        e = self.extension
        fx = (x + e) / (2 * e) * (n - 1)
        fz = (z + e) / (2 * e) * (n - 1)
        i = int(min(max(int(fx), 0), n - 2))
        j = int(min(max(int(fz), 0), n - 2))
        tx = min(max(fx - i, 0.0), 1.0)
        tz = min(max(fz - j, 0.0), 1.0)
        h = self.altura
        a = h[j, i] * (1 - tx) + h[j, i + 1] * tx
        b = h[j + 1, i] * (1 - tx) + h[j + 1, i + 1] * tx
        return float(a * (1 - tz) + b * tz)

    def collides(self, punto):
        return False

    def liberar(self):
        for b in (self._vbo, self._ibo):
            if b is not None:
                try:
                    b.delete()
                except Exception:
                    pass
        self._vbo = self._ibo = None

    def draw(self):
        if self._vbo is None:
            return
        glEnable(GL_LIGHTING)
        Iluminacion.set_modo(Iluminacion.MODO_TERRENO)

        # Unidad 1: detalle (solo lo usa el shader)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.tex_detalle)
        glActiveTexture(GL_TEXTURE0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.tex_color)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.02, 0.02, 0.02, 1.0])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 8.0)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        self._vbo.bind()
        glVertexPointer(3, GL_FLOAT, STRIDE, self._vbo)
        glTexCoordPointer(2, GL_FLOAT, STRIDE, self._vbo + 12)
        glNormalPointer(GL_FLOAT, STRIDE, self._vbo + 20)
        self._ibo.bind()
        glDrawElements(GL_TRIANGLES, self._n_indices, GL_UNSIGNED_INT, None)
        self._ibo.unbind()
        self._vbo.unbind()
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, 0)
        glActiveTexture(GL_TEXTURE0)
        glDisable(GL_TEXTURE_2D)
        Iluminacion.set_modo(Iluminacion.MODO_NORMAL)
        glDisable(GL_LIGHTING)
