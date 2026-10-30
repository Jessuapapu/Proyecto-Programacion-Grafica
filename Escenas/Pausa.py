"""
Menú de pausa dentro del juego (ESC o botón Start del control).

Como la ventana del juego usa OpenGL, el menú se dibuja primero en una superficie
de pygame y luego se sube como textura y se pinta encima de la escena congelada.
"""
import pygame
from OpenGL.GL import *

COLOR_PANEL = (103, 77, 64)
COLOR_HOVER = (133, 107, 94)
COLOR_BORDE = (255, 255, 255)
COLOR_TEXTO = (255, 255, 255)
COLOR_BARRA = (70, 52, 43)
COLOR_RELLENO = (214, 168, 110)


class _Boton:
    def __init__(self, texto, accion):
        self.texto = texto
        self.accion = accion
        self.rect = pygame.Rect(0, 0, 0, 0)


class _Slider:
    def __init__(self, clave, etiqueta, minimo, maximo, paso):
        self.clave = clave
        self.etiqueta = etiqueta
        self.min = minimo
        self.max = maximo
        self.paso = paso
        self.rect = pygame.Rect(0, 0, 0, 0)

    def valor_desde_x(self, x):
        t = max(0.0, min(1.0, (x - self.rect.x) / max(1, self.rect.width)))
        valor = self.min + t * (self.max - self.min)
        return round(round(valor / self.paso) * self.paso, 2)


class MenuPausa:
    def __init__(self, volumen, sensibilidad, velocidad, siempre_dia=False):
        self.abierto = False
        self.siempre_dia = siempre_dia
        self.vista = "principal"            # "principal" o "config"
        self.valores = {"volumen": volumen, "sensibilidad": sensibilidad, "velocidad": velocidad}

        self.botones = {
            "principal": [_Boton("CONTINUAR", "continuar"),
                          _Boton("CONFIGURACION", "config"),
                          _Boton("SALIR DEL JUEGO", "salir")],
            "config": [_Boton("", "cielo"),
                       _Boton("REGRESAR", "regresar")],
        }
        self.sliders = [_Slider("volumen", "VOLUMEN", 0, 10, 1),
                        _Slider("sensibilidad", "SENSIBILIDAD", 0.1, 2.0, 0.1),
                        _Slider("velocidad", "VELOCIDAD", 1, 20, 0.5)]

        self._arrastrando = None
        self._tam_ventana = None
        self._textura = None
        self.panel = pygame.Rect(0, 0, 0, 0)

    # ------------------------------------------------------------ Diseño
    def _diseno(self, ancho, alto):
        if self._tam_ventana == (ancho, alto):
            return
        self._tam_ventana = (ancho, alto)
        s = max(0.75, min(1.8, alto / 768.0))
        self.s = s
        pw, ph = int(460 * s), int(470 * s)
        self.panel = pygame.Rect((ancho - pw) // 2, (alto - ph) // 2, pw, ph)

        self.fuente = pygame.font.SysFont("Consolas", int(18 * s), bold=True)
        self.fuente_titulo = pygame.font.SysFont("Consolas", int(34 * s), bold=True)
        self.fuente_peq = pygame.font.SysFont("Consolas", int(14 * s))

        bw, bh = int(300 * s), int(48 * s)
        x = (pw - bw) // 2
        for i, b in enumerate(self.botones["principal"]):
            b.rect = pygame.Rect(x, int(130 * s) + i * int(68 * s), bw, bh)
        self.botones["config"][0].rect = pygame.Rect(x, int(318 * s), bw, bh)
        self.botones["config"][1].rect = pygame.Rect(x, int(380 * s), bw, bh)

        for i, sl in enumerate(self.sliders):
            sl.rect = pygame.Rect(int(60 * s), int(135 * s) + i * int(60 * s), pw - int(120 * s), max(6, int(10 * s)))

    # ------------------------------------------------------------ Estado
    def abrir(self):
        self.abierto = True
        self.vista = "principal"
        self._arrastrando = None

    def cerrar(self):
        self.abierto = False
        self._arrastrando = None

    def _local(self, pos):
        return pos[0] - self.panel.x, pos[1] - self.panel.y

    def manejar_evento(self, evento):
        """Procesa clics y arrastres del ratón. Devuelve 'continuar', 'salir' o None."""
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pos = self._local(evento.pos)
            for b in self.botones[self.vista]:
                if b.rect.collidepoint(pos):
                    if b.accion == "config":
                        self.vista = "config"
                        return None
                    if b.accion == "regresar":
                        self.vista = "principal"
                        return None
                    if b.accion == "cielo":
                        self.siempre_dia = not self.siempre_dia
                        return None
                    return b.accion
            if self.vista == "config":
                for sl in self.sliders:
                    if sl.rect.inflate(int(16 * self.s), int(24 * self.s)).collidepoint(pos):
                        self._arrastrando = sl
                        self.valores[sl.clave] = sl.valor_desde_x(pos[0])
        elif evento.type == pygame.MOUSEMOTION and self._arrastrando is not None:
            pos = self._local(evento.pos)
            self.valores[self._arrastrando.clave] = self._arrastrando.valor_desde_x(pos[0])
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            self._arrastrando = None
        return None

    def atras(self):
        """ESC dentro del menú: si está en configuración vuelve al menú principal.
        Devuelve True si el menú debe cerrarse."""
        if self.vista == "config":
            self.vista = "principal"
            return False
        return True

    # ------------------------------------------------------------ Dibujo
    def _texto_centrado(self, sup, fuente, texto, cx, y, color=COLOR_TEXTO):
        img = fuente.render(texto, True, color)
        sup.blit(img, (cx - img.get_width() // 2, y))

    def _superficie(self, hora):
        s = self.s
        pw, ph = self.panel.size
        sup = pygame.Surface((pw, ph), pygame.SRCALPHA)
        radio = int(14 * s)
        pygame.draw.rect(sup, (*COLOR_PANEL, 245), sup.get_rect(), border_radius=radio)
        pygame.draw.rect(sup, COLOR_BORDE, sup.get_rect(), max(2, int(2 * s)), border_radius=radio)

        titulo = "PAUSA" if self.vista == "principal" else "CONFIGURACION"
        self._texto_centrado(sup, self.fuente_titulo, titulo, pw // 2, int(28 * s))
        h, m = int(hora), int((hora % 1) * 60)
        modo = "siempre de dia" if self.siempre_dia else "ciclo dia/noche"
        self._texto_centrado(sup, self.fuente_peq, f"Hora en la hacienda: {h:02d}:{m:02d} ({modo})", pw // 2, int(78 * s))
        self.botones["config"][0].texto = "CIELO: SIEMPRE DE DIA" if self.siempre_dia else "CIELO: CICLO DIA/NOCHE"

        raton = self._local(pygame.mouse.get_pos())
        for b in self.botones[self.vista]:
            color = COLOR_HOVER if b.rect.collidepoint(raton) else COLOR_PANEL
            pygame.draw.rect(sup, color, b.rect, border_radius=int(10 * s))
            pygame.draw.rect(sup, COLOR_BORDE, b.rect, max(2, int(2 * s)), border_radius=int(10 * s))
            img = self.fuente.render(b.texto, True, COLOR_TEXTO)
            sup.blit(img, (b.rect.centerx - img.get_width() // 2, b.rect.centery - img.get_height() // 2))

        if self.vista == "config":
            for sl in self.sliders:
                valor = self.valores[sl.clave]
                texto = f"{sl.etiqueta}: {valor:g}"
                sup.blit(self.fuente.render(texto, True, COLOR_TEXTO), (sl.rect.x, sl.rect.y - int(28 * s)))
                pygame.draw.rect(sup, COLOR_BARRA, sl.rect, border_radius=sl.rect.height // 2)
                t = (valor - sl.min) / (sl.max - sl.min)
                lleno = sl.rect.copy()
                lleno.width = max(1, int(sl.rect.width * t))
                pygame.draw.rect(sup, COLOR_RELLENO, lleno, border_radius=sl.rect.height // 2)
                pygame.draw.circle(sup, COLOR_BORDE, (sl.rect.x + lleno.width, sl.rect.centery), int(9 * s))

        pie = "ESC: continuar" if self.vista == "principal" else "ESC: regresar"
        self._texto_centrado(sup, self.fuente_peq, pie, pw // 2, ph - int(30 * s), (230, 215, 200))
        return sup

    def dibujar(self, ancho, alto, hora):
        """Dibuja el menú encima de la escena (llamar después de dibujar el mundo)."""
        self._diseno(ancho, alto)
        sup = self._superficie(hora)
        w, h = sup.get_size()
        if hasattr(pygame.image, "tobytes"):
            datos = pygame.image.tobytes(sup, "RGBA", False)
        else:
            datos = pygame.image.tostring(sup, "RGBA", False)

        if self._textura is None:
            self._textura = glGenTextures(1)

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_FOG)
        glDisable(GL_ALPHA_TEST)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, ancho, alto, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Oscurece la escena de fondo
        glDisable(GL_TEXTURE_2D)
        glColor4f(0.0, 0.0, 0.0, 0.55)
        glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(ancho, 0); glVertex2f(ancho, alto); glVertex2f(0, alto)
        glEnd()

        # Panel del menú
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self._textura)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, datos)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        x, y = self.panel.x, self.panel.y
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x, y)
        glTexCoord2f(1, 0); glVertex2f(x + w, y)
        glTexCoord2f(1, 1); glVertex2f(x + w, y + h)
        glTexCoord2f(0, 1); glVertex2f(x, y + h)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()

    def liberar(self):
        if self._textura is not None:
            try:
                glDeleteTextures([self._textura])
            except Exception:
                pass
            self._textura = None
