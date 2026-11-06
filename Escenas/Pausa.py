# menu de pausa (ESC o start), con el mismo estilo que el menu principal
# se dibuja con pygame en una superficie y se pasa como textura encima de la escena
import pygame
from OpenGL.GL import *

from Clases import Ventana
from Escenas import Menu as M


class MenuPausa:

    def __init__(self, volumen, sensibilidad, velocidad, siempre_dia=False):
        self.abierto = False
        self.siempre_dia = siempre_dia
        self.valores = {"volumen": volumen, "sensibilidad": sensibilidad, "velocidad": velocidad}
        self.vista = "principal"            # principal o config
        self.foco = 0
        self.anim = 0.0                     # 0 a 1 al abrir
        self.tiempo = 0.0
        self._accion = None
        self._arrastrando = None
        self._ultimo_eje = 0.0
        self._textura = None
        self._f = None
        self._sonidos = None
        self._rect = pygame.Rect(0, 0, 0, 0)    # donde quedo el panel en la ventana
        self._escala = 1.0
        self._hora = 12.0

        def accion(nombre):
            return lambda: setattr(self, "_accion", nombre)

        w = 520
        self.principal = [
            M.Boton("CONTINUAR", accion("continuar"), ((w - 360) // 2, 128, 360, 56)),
            M.Boton("CONFIGURACIÓN", lambda: self._cambiar_vista("config"), ((w - 360) // 2, 196, 360, 56)),
            M.Boton("VOLVER AL MENÚ", accion("menu"), ((w - 360) // 2, 264, 360, 56)),
            M.Boton("SALIR DEL JUEGO", accion("salir"), ((w - 360) // 2, 332, 360, 56)),
        ]
        w2 = 700
        self.config = [
            M.Deslizador("VOLUMEN", self.valores, "volumen", 0, 10, 1, (30, 100, w2 - 60, 58)),
            M.Deslizador("SENSIBILIDAD", self.valores, "sensibilidad", 0.1, 2.0, 0.1, (30, 168, w2 - 60, 58),
                         formato="{:.1f}"),
            M.Deslizador("VELOCIDAD", self.valores, "velocidad", 1, 20, 0.5, (30, 236, w2 - 60, 58)),
            M.Selector("CIELO", ["CICLO DÍA/NOCHE", "SIEMPRE DE DÍA"], lambda: int(self.siempre_dia),
                       lambda v: setattr(self, "siempre_dia", bool(v)), (30, 304, w2 - 60, 58)),
            M.Selector("PANTALLA", ["VENTANA", "COMPLETA"], lambda: int(Ventana.pantalla_completa),
                       lambda v: Ventana.poner_pantalla_completa(bool(v)), (30, 372, w2 - 60, 58)),
            M.Boton("REGRESAR", lambda: self._cambiar_vista("principal"), ((w2 - 260) // 2, 456, 260, 54)),
        ]
        self.tamanos = {"principal": (w, 440), "config": (w2, 540)}

    # estado
    @property
    def widgets(self):
        return self.principal if self.vista == "principal" else self.config

    def abrir(self):
        self.abierto = True
        self.vista = "principal"
        self.foco = 0
        self.anim = 0.0
        self.tiempo = 0.0
        self._arrastrando = None

    def cerrar(self):
        self.abierto = False
        self._arrastrando = None

    def _cambiar_vista(self, vista):
        self.vista = vista
        self.foco = 0
        self.tiempo = 0.0

    def atras(self):
        # ESC: si esta en config regresa, si no cierra la pausa
        if self.vista == "config":
            self.sonar("atras")
            self._cambiar_vista("principal")
            return False
        return True

    def sonar(self, nombre):
        # los widgets del menu llaman a esto
        if self._sonidos is None:
            self._sonidos = {"hover": M._tono(900, 1200, 0.05, 0.10), "click": M._tono(520, 880, 0.12, 0.22),
                             "tick": M._tono(1300, 1300, 0.03, 0.08), "atras": M._tono(700, 420, 0.12, 0.18)}
        s = self._sonidos.get(nombre)
        if s and pygame.mixer.get_init():
            s.set_volume(0.3 + 0.7 * self.valores["volumen"] / 10.0)
            s.play()

    # entrada
    def _local(self, pos):
        # coordenadas de la ventana a coordenadas del panel
        return ((pos[0] - self._rect.x) / self._escala, (pos[1] - self._rect.y) / self._escala)

    def _mover_foco(self, paso):
        self.foco = (self.foco + paso) % len(self.widgets)
        self.sonar("hover")

    def manejar_evento(self, e):
        # devuelve 'continuar', 'menu', 'salir' o None
        self._accion = None
        ws = self.widgets
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self._mover_foco(-1)
            elif e.key in (pygame.K_DOWN, pygame.K_s, pygame.K_TAB):
                self._mover_foco(1)
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                ws[self.foco].ajustar(-1, self)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                ws[self.foco].ajustar(1, self)
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                ws[self.foco].activar(self)
        elif e.type == pygame.JOYHATMOTION:
            hx, hy = e.value
            if hy:
                self._mover_foco(-hy)
            elif hx:
                ws[self.foco].ajustar(hx, self)
        elif e.type == pygame.JOYAXISMOTION and e.axis in (0, 1):
            ahora = pygame.time.get_ticks() / 1000.0
            if abs(e.value) > 0.6 and ahora - self._ultimo_eje > 0.22:
                self._ultimo_eje = ahora
                if e.axis == 1:
                    self._mover_foco(1 if e.value > 0 else -1)
                else:
                    ws[self.foco].ajustar(1 if e.value > 0 else -1, self)
        elif e.type == pygame.JOYBUTTONDOWN:
            if e.button == 0:
                ws[self.foco].activar(self)
            elif e.button == 1 and self.vista == "config":
                self.atras()
        elif e.type == pygame.MOUSEMOTION:
            local = self._local(e.pos)
            if self._arrastrando:
                self._arrastrando.desde_x(local[0])
            else:
                for i, w in enumerate(ws):
                    if w.contiene(local) and i != self.foco:
                        self.foco = i
                        self.sonar("hover")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            local = self._local(e.pos)
            for i, w in enumerate(ws):
                if not w.contiene(local):
                    continue
                self.foco = i
                if isinstance(w, M.Deslizador):
                    self._arrastrando = w
                    if w.barra.inflate(30, 30).collidepoint(local):
                        w.desde_x(local[0])
                elif isinstance(w, M.Selector):
                    w.clic(local, self)
                else:
                    w.activar(self)
                break
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if self._arrastrando:
                self.sonar("tick")
            self._arrastrando = None
        elif e.type == pygame.MOUSEWHEEL:
            w = ws[self.foco]
            if isinstance(w, (M.Deslizador, M.Selector)):
                w.ajustar(1 if e.y > 0 else -1, self)
        return self._accion

    # dibujo
    def _fuentes(self):
        if self._f is None:
            serif = "georgia,palatinolinotype,timesnewroman,dejavuserif,serif"
            sans = "segoeui,trebuchetms,verdana,dejavusans,arial"
            self._f = {
                "panel": M._fuente(serif, 36, True),
                "boton": M._fuente(sans, 25, True),
                "normal": M._fuente(sans, 22, True),
                "texto": M._fuente(sans, 20),
                "chico": M._fuente(sans, 18, True),
            }
        return self._f

    def _superficie(self, dt):
        f = self._fuentes()
        pw, ph = self.tamanos[self.vista]
        sup = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(sup, (36, 25, 19, 240), sup.get_rect(), border_radius=18)
        pygame.draw.rect(sup, M.DORADO, sup.get_rect(), 2, border_radius=18)
        pygame.draw.rect(sup, (*M.DORADO, 60), sup.get_rect().inflate(-12, -12), 1, border_radius=14)

        titulo = "PAUSA" if self.vista == "principal" else "CONFIGURACIÓN"
        t = M._texto(f["panel"], titulo, M.DORADO)
        sup.blit(t, t.get_rect(midtop=(pw // 2, 22)))
        ancho = int(t.get_width() * M._salida_cubica(self.tiempo / 0.5))
        pygame.draw.line(sup, M.DORADO, (pw // 2 - ancho // 2, 70), (pw // 2 + ancho // 2, 70), 2)

        if self.vista == "principal":
            h, m = int(self._hora), int((self._hora % 1) * 60)
            modo = "siempre de día" if self.siempre_dia else "ciclo día/noche"
            t = M._texto(f["texto"], f"Hora en la hacienda: {h:02d}:{m:02d} ({modo})", M.TENUE)
            sup.blit(t, t.get_rect(center=(pw // 2, 96)))

        for i, w in enumerate(self.widgets):
            w.dibujar(sup, i == self.foco, dt, f)

        pie = "↑↓ Elegir   Enter Aceptar   Esc Continuar" if self.vista == "principal" \
            else "↑↓ Elegir   ←→ Ajustar   Esc Regresar"
        t = M._texto(f["chico"], pie, M.GRIS)
        sup.blit(t, t.get_rect(midbottom=(pw // 2, ph - 16)))
        return sup

    def dibujar(self, ancho, alto, hora, dt=1 / 60):
        self._hora = hora
        self.anim = min(1.0, self.anim + dt * 4)
        self.tiempo += dt
        a = M._salida_cubica(self.anim)

        sup = self._superficie(dt)
        w, h = sup.get_size()
        self._escala = max(0.7, min(1.8, alto / 768.0))
        dw, dh = int(w * self._escala), int(h * self._escala)
        x = (ancho - dw) // 2
        y = (alto - dh) // 2 + int((1 - a) * 40 * self._escala)
        self._rect = pygame.Rect(x, y, dw, dh)

        # pygame-ce usa tobytes y pygame viejo tostring
        if hasattr(pygame.image, "tobytes"):
            datos = pygame.image.tobytes(sup, "RGBA", False)
        else:
            datos = pygame.image.tostring(sup, "RGBA", False)
        if self._textura is None:
            self._textura = glGenTextures(1)

        # proyeccion 2d en pixeles
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        for cap in (GL_LIGHTING, GL_DEPTH_TEST, GL_FOG, GL_ALPHA_TEST, GL_CULL_FACE):
            glDisable(cap)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, ancho, alto, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # oscurecer el fondo
        glDisable(GL_TEXTURE_2D)
        glColor4f(0.03, 0.02, 0.01, 0.55 * a)
        glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(ancho, 0); glVertex2f(ancho, alto); glVertex2f(0, alto)
        glEnd()

        # panel
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self._textura)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, datos)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glColor4f(1.0, 1.0, 1.0, a)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x, y)
        glTexCoord2f(1, 0); glVertex2f(x + dw, y)
        glTexCoord2f(1, 1); glVertex2f(x + dw, y + dh)
        glTexCoord2f(0, 1); glVertex2f(x, y + dh)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()

    def liberar(self):
        if self._textura is not None:
            glDeleteTextures([self._textura])
            self._textura = None
