# menu principal
# se puede usar con mouse, teclado o control
import math
import os
import random
import sys

import numpy as np
import pygame

from Clases import Joycon
from Audio import Audios

# ruta base
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

ANCHO, ALTO = 1408, 768

# colores
DORADO = (226, 182, 116)
DORADO_OSCURO = (150, 112, 62)
MADERA = (64, 44, 34)
MADERA_CLARA = (112, 80, 60)
BLANCO = (255, 255, 255)
TENUE = (222, 208, 192)
GRIS = (160, 150, 140)


# utilidades
def _fuente(nombres, tam, negrita=False):
    return pygame.font.SysFont(nombres, tam, bold=negrita)


def _limitar(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def _salida_cubica(t):
    # animacion que frena al final
    t = _limitar(t)
    return 1 - (1 - t) ** 3


def _acercar(actual, objetivo, dt, rapidez=12.0):
    # acerca un valor a otro poco a poco
    return actual + (objetivo - actual) * min(1.0, dt * rapidez)


def _mezclar_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


_cache_textos = {}


def _texto(fuente, txt, color):
    # guarda los textos para no renderizarlos cada frame
    clave = (id(fuente), txt, color)
    sup = _cache_textos.get(clave)
    if sup is None:
        if len(_cache_textos) > 600:
            _cache_textos.clear()
        sup = fuente.render(txt, True, color)
        _cache_textos[clave] = sup
    sup.set_alpha(255)
    return sup


def _tono(f0, f1, duracion, volumen=0.25):
    # sonidito del menu hecho con numpy
    try:
        ini = pygame.mixer.get_init()
        if not ini:
            return None
        frecuencia, tam, canales = ini
        n = int(frecuencia * duracion)
        t = np.arange(n) / frecuencia
        f = np.linspace(f0, f1, n)
        fase = 2 * np.pi * np.cumsum(f) / frecuencia
        env = np.minimum(1.0, t / 0.004) * np.exp(-t / (duracion * 0.35))
        onda = (np.sin(fase) + 0.25 * np.sin(fase * 2)) * env * volumen
        if tam in (-16, 16):
            datos = (onda * 32767).astype(np.int16)
        elif tam in (-32, 32):
            datos = onda.astype(np.float32)
        elif tam == 8:
            datos = ((onda * 127) + 128).astype(np.uint8)
        else:
            datos = (onda * 127).astype(np.int8)
        if canales > 1:
            datos = np.repeat(datos[:, None], canales, axis=1)
        return pygame.sndarray.make_sound(np.ascontiguousarray(datos))
    except Exception as e:
        print(f"⚠️ No se pudieron crear los sonidos del menú: {e}")
        return None


# widgets
class Boton:
    def __init__(self, texto, accion, rect, descripcion=""):
        self.texto = texto
        self.accion = accion
        self.rect = pygame.Rect(rect)
        self.descripcion = descripcion
        self.brillo = 0.0

    def ajustar(self, direccion, menu):
        return False

    def activar(self, menu):
        menu.sonar("click")
        self.accion()

    def contiene(self, pos):
        return self.rect.collidepoint(pos)

    def dibujar(self, sup, enfocado, dt, f):
        self.brillo = _acercar(self.brillo, 1.0 if enfocado else 0.0, dt, 14)
        b = self.brillo
        r = self.rect.inflate(int(10 * b), int(4 * b))
        fondo = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(fondo, (*_mezclar_color(MADERA, MADERA_CLARA, b), 225), fondo.get_rect(), border_radius=12)
        sup.blit(fondo, r.topleft)
        pygame.draw.rect(sup, _mezclar_color(GRIS, DORADO, b), r, 2, border_radius=12)
        t = _texto(f["boton"], self.texto() if callable(self.texto) else self.texto, BLANCO)
        sup.blit(t, t.get_rect(center=r.center))


class Deslizador:
    def __init__(self, etiqueta, valores, clave, minimo, maximo, paso, rect, al_cambiar=None, formato="{:g}"):
        self.etiqueta = etiqueta
        self.valores = valores
        self.clave = clave
        self.min, self.max, self.paso = minimo, maximo, paso
        self.rect = pygame.Rect(rect)
        self.al_cambiar = al_cambiar
        self.formato = formato
        self.brillo = 0.0
        self.mostrado = self._fraccion()

    @property
    def barra(self):
        return pygame.Rect(self.rect.x + 250, self.rect.centery - 5, self.rect.width - 340, 10)

    def _fraccion(self):
        return (self.valores[self.clave] - self.min) / (self.max - self.min)

    def _poner(self, valor):
        # redondea, limita y avisa si cambio
        valor = round(round(valor / self.paso) * self.paso, 2)
        valor = _limitar(valor, self.min, self.max)
        if valor != self.valores[self.clave]:
            self.valores[self.clave] = valor
            if self.al_cambiar:
                self.al_cambiar(valor)
            return True
        return False

    def desde_x(self, x):
        t = _limitar((x - self.barra.x) / self.barra.width)
        return self._poner(self.min + t * (self.max - self.min))

    def ajustar(self, direccion, menu):
        if self._poner(self.valores[self.clave] + direccion * self.paso):
            menu.sonar("tick")
        return True

    def activar(self, menu):
        pass

    def contiene(self, pos):
        return self.rect.collidepoint(pos)

    def dibujar(self, sup, enfocado, dt, f):
        self.brillo = _acercar(self.brillo, 1.0 if enfocado else 0.0, dt, 14)
        self.mostrado = _acercar(self.mostrado, self._fraccion(), dt, 18)
        if self.brillo > 0.01:
            resalte = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(resalte, (255, 255, 255, int(22 * self.brillo)), resalte.get_rect(), border_radius=10)
            sup.blit(resalte, self.rect.topleft)
        et = _texto(f["normal"], self.etiqueta, _mezclar_color(TENUE, DORADO, self.brillo))
        sup.blit(et, et.get_rect(midleft=(self.rect.x + 18, self.rect.centery)))
        barra = self.barra
        pygame.draw.rect(sup, (40, 30, 24), barra, border_radius=5)
        lleno = barra.copy()
        lleno.width = max(10, int(barra.width * self.mostrado))
        pygame.draw.rect(sup, _mezclar_color(DORADO_OSCURO, DORADO, self.brillo), lleno, border_radius=5)
        kx = barra.x + int(barra.width * self.mostrado)
        radio = 11 + int(3 * self.brillo)
        if self.brillo > 0.01:
            halo = pygame.Surface((radio * 4, radio * 4), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*DORADO, int(70 * self.brillo)), (radio * 2, radio * 2), radio * 2)
            sup.blit(halo, (kx - radio * 2, barra.centery - radio * 2))
        pygame.draw.circle(sup, BLANCO, (kx, barra.centery), radio)
        pygame.draw.circle(sup, DORADO_OSCURO, (kx, barra.centery), radio, 2)
        val = _texto(f["normal"], self.formato.format(self.valores[self.clave]), BLANCO)
        sup.blit(val, val.get_rect(midright=(self.rect.right - 18, self.rect.centery)))


class Selector:
    # selector de dos opciones

    def __init__(self, etiqueta, opciones, obtener, poner, rect):
        self.etiqueta = etiqueta
        self.opciones = opciones
        self.obtener = obtener
        self.poner = poner
        self.rect = pygame.Rect(rect)
        self.brillo = 0.0
        self.pos = float(obtener())

    @property
    def caja(self):
        return pygame.Rect(self.rect.x + 250, self.rect.y + 6, self.rect.width - 268, self.rect.height - 12)

    def ajustar(self, direccion, menu):
        nuevo = 1 if direccion > 0 else 0
        if nuevo != self.obtener():
            self.poner(nuevo)
            menu.sonar("tick")
        return True

    def activar(self, menu):
        self.poner(1 - self.obtener())
        menu.sonar("click")

    def clic(self, pos, menu):
        caja = self.caja
        if caja.collidepoint(pos):
            nuevo = 0 if pos[0] < caja.centerx else 1
            if nuevo != self.obtener():
                self.poner(nuevo)
                menu.sonar("click")

    def contiene(self, pos):
        return self.rect.collidepoint(pos)

    def dibujar(self, sup, enfocado, dt, f):
        self.brillo = _acercar(self.brillo, 1.0 if enfocado else 0.0, dt, 14)
        self.pos = _acercar(self.pos, float(self.obtener()), dt, 14)
        if self.brillo > 0.01:
            resalte = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(resalte, (255, 255, 255, int(22 * self.brillo)), resalte.get_rect(), border_radius=10)
            sup.blit(resalte, self.rect.topleft)
        et = _texto(f["normal"], self.etiqueta, _mezclar_color(TENUE, DORADO, self.brillo))
        sup.blit(et, et.get_rect(midleft=(self.rect.x + 18, self.rect.centery)))
        caja = self.caja
        pygame.draw.rect(sup, (40, 30, 24), caja, border_radius=caja.height // 2)
        mitad = caja.width // 2
        marca = pygame.Rect(caja.x + 3 + int(self.pos * mitad), caja.y + 3, mitad - 6, caja.height - 6)
        pygame.draw.rect(sup, _mezclar_color(DORADO_OSCURO, DORADO, 0.5 + 0.5 * self.brillo), marca,
                         border_radius=marca.height // 2)
        for i, op in enumerate(self.opciones):
            activo = abs(self.pos - i) < 0.5
            t = _texto(f["chico"], op, (40, 26, 18) if activo else TENUE)
            sup.blit(t, t.get_rect(center=(caja.x + mitad // 2 + i * mitad, caja.centery)))


# paneles
class Panel:
    def __init__(self, titulo, tamano, widgets, dibujar_extra=None, foco=0):
        # anim va de 0 a 1 al abrir y regresa a 0 al cerrar
        self.titulo = titulo
        self.rect = pygame.Rect(0, 0, *tamano)
        self.rect.center = (ANCHO // 2 + 120, ALTO // 2 + 10)
        self.widgets = widgets
        self.dibujar_extra = dibujar_extra
        self.foco = foco
        self.anim = 0.0
        self.cerrando = False
        self.al_cerrar = None
        self.tiempo = 0.0


# menu
class Menu:
    def __init__(self, control, sensibilidad, sonido, velocidad, siempre_dia=False):
        # estos valores se le pasan al juego
        self.control = control
        self.start_game = False
        self.saliendo = 0.0               # fundido a negro al darle iniciar
        self.valores = {"volumen": sonido, "sensibilidad": sensibilidad, "velocidad": velocidad}
        self.siempre_dia = siempre_dia
        self.t = 0.0
        self.panel = None
        self.foco = 0
        self.arrastrando = None
        self.ultimo_eje = 0.0

        self.f = {
            "titulo": _fuente("georgia,palatinolinotype,timesnewroman,dejavuserif,serif", 78, True),
            "subtitulo": _fuente("georgia,palatinolinotype,timesnewroman,dejavuserif,serif", 30, True),
            "fecha": _fuente("georgia,palatinolinotype,timesnewroman,dejavuserif,serif", 21),
            "boton": _fuente("segoeui,trebuchetms,verdana,dejavusans,arial", 25, True),
            "normal": _fuente("segoeui,trebuchetms,verdana,dejavusans,arial", 22, True),
            "texto": _fuente("segoeui,trebuchetms,verdana,dejavusans,arial", 21),
            "chico": _fuente("segoeui,trebuchetms,verdana,dejavusans,arial", 18, True),
            "tecla": _fuente("consolas,dejavusansmono,couriernew,monospace", 18, True),
            "panel": _fuente("georgia,palatinolinotype,timesnewroman,dejavuserif,serif", 36, True),
        }

        self.opciones = [
            ("INICIAR RECORRIDO", self.iniciar, "Entra a la hacienda y recórrela en primera persona."),
            ("CONFIGURACIÓN", self.abrir_config, "Volumen, sensibilidad, velocidad y modo del cielo."),
            ("AYUDA", self.abrir_ayuda, "Controles de teclado, ratón y control."),
            ("CRÉDITOS", self.abrir_creditos, "Integrantes del proyecto y agradecimientos."),
            ("SALIR", self.confirmar_salida, "Cerrar el juego."),
        ]
        self.brillos = [0.0] * len(self.opciones)
        self.rects = [pygame.Rect(96, 300 + i * 74, 360, 58) for i in range(len(self.opciones))]

        self._cargar_fondo()
        self._crear_particulas()
        self.sonidos = {"hover": _tono(900, 1200, 0.05, 0.10), "click": _tono(520, 880, 0.12, 0.22),
                        "tick": _tono(1300, 1300, 0.03, 0.08), "atras": _tono(700, 420, 0.12, 0.18)}

    # recursos
    def _cargar_fondo(self):
        ruta = os.path.join(BASE_PATH, "Recursos", "Imagenes", "hacienda.jpeg")
        try:
            img = pygame.image.load(ruta).convert()
        except Exception as e:
            print(f"⚠️ No se encontró el fondo del menú: {e}")
            img = pygame.Surface((ANCHO, ALTO))
            img.fill((60, 80, 60))
        # un poco mas grande que la ventana para poder moverlo
        esc = max(ANCHO * 1.12 / img.get_width(), ALTO * 1.12 / img.get_height())
        self.fondo = pygame.transform.smoothscale(img, (int(img.get_width() * esc), int(img.get_height() * esc)))

        # sombra a la izquierda y abajo para que se lean los botones
        self.sombra = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        x = np.linspace(0, 1, ANCHO)[:, None]
        y = np.linspace(0, 1, ALTO)[None, :]
        alfa = 205 * np.clip(1 - x / 0.62, 0, 1) ** 1.4
        alfa = np.maximum(alfa, 150 * np.clip((y - 0.72) / 0.28, 0, 1) ** 1.5)
        alfa = np.maximum(alfa, 90 * np.clip((0.12 - y) / 0.12, 0, 1))
        pixeles = pygame.surfarray.pixels_alpha(self.sombra)
        pixeles[:] = alfa.astype(np.uint8)
        del pixeles
        self.sombra.fill((14, 9, 6, 0), special_flags=pygame.BLEND_RGBA_MAX)

    def _crear_particulas(self):
        # x, y, velocidad, tamaño, fase, deriva
        rnd = random.Random(4)
        self.particulas = [[rnd.uniform(0, ANCHO), rnd.uniform(0, ALTO), rnd.uniform(6, 22),
                            rnd.uniform(1.2, 3.2), rnd.uniform(0, 6.28), rnd.uniform(-8, 8)] for _ in range(70)]

    def sonar(self, nombre):
        s = self.sonidos.get(nombre)
        if s and pygame.mixer.get_init():
            s.set_volume(0.3 + 0.7 * self.valores["volumen"] / 10.0)
            s.play()

    # acciones
    def iniciar(self):
        if self.saliendo == 0.0:
            self.saliendo = 0.001
            if pygame.mixer.get_init():
                pygame.mixer.music.fadeout(700)

    def _abrir(self, panel):
        self.panel = panel
        self.arrastrando = None

    def cerrar_panel(self, despues=None):
        if self.panel and not self.panel.cerrando:
            self.panel.cerrando = True
            self.panel.al_cerrar = despues
            self.sonar("atras")

    def abrir_config(self):
        self.control.JoyStick = pygame.joystick.Joystick(0) if pygame.joystick.get_count() > 0 else None
        if self.control.JoyStick:
            self.control.JoyStick.init()
        w = 700
        widgets = [
            Deslizador("VOLUMEN", self.valores, "volumen", 0, 10, 1, (30, 100, w - 60, 58),
                       al_cambiar=lambda v: pygame.mixer.get_init() and pygame.mixer.music.set_volume(v / 10.0)),
            Deslizador("SENSIBILIDAD", self.valores, "sensibilidad", 0.1, 2.0, 0.1, (30, 168, w - 60, 58),
                       formato="{:.1f}"),
            Deslizador("VELOCIDAD", self.valores, "velocidad", 1, 20, 0.5, (30, 236, w - 60, 58), formato="{:g}"),
            Selector("CIELO", ["CICLO DÍA/NOCHE", "SIEMPRE DE DÍA"], lambda: int(self.siempre_dia),
                     self._poner_cielo, (30, 304, w - 60, 58)),
            Boton("REGRESAR", lambda: self.cerrar_panel(), ((w - 260) // 2, 432, 260, 54)),
        ]

        def extra(sup, panel, f):
            if self.control.JoyStick:
                txt, color = f"Control conectado: {self.control.JoyStick.get_name()}", (150, 220, 140)
            else:
                txt, color = "Control: no conectado (puedes usar teclado y ratón)", GRIS
            t = _texto(f["chico"], txt, color)
            sup.blit(t, t.get_rect(center=(panel.rect.width // 2, 394)))
            pygame.draw.circle(sup, color, (panel.rect.width // 2 - t.get_width() // 2 - 14, 394), 5)

        self._abrir(Panel("CONFIGURACIÓN", (w, 510), widgets, extra))

    def _poner_cielo(self, valor):
        self.siempre_dia = bool(valor)

    def abrir_ayuda(self):
        w = 760
        teclas = [
            (["W"], "Avanzar"), (["S"], "Retroceder"), (["A"], "Izquierda"), (["D"], "Derecha"),
            (["ESPACIO"], "Subir"), (["SHIFT"], "Bajar"), (["RATÓN"], "Mirar alrededor"), (["ESC"], "Menú de pausa"),
        ]
        mando = [("Palanca izquierda", "Moverse"), ("Palanca derecha", "Mirar"), ("Start", "Menú de pausa")]

        def extra(sup, panel, f):
            aparicion = panel.tiempo
            x0, y0 = 40, 100
            for i, (keys, accion) in enumerate(teclas):
                a = _salida_cubica((aparicion - i * 0.04) / 0.3)
                if a <= 0:
                    continue
                col, fila = i % 2, i // 2
                x = x0 + col * 350 + int((1 - a) * 30)
                y = y0 + fila * 56
                for k in keys:
                    x = self._tecla(sup, k, x, y, f, a) + 14
                t = _texto(f["texto"], accion, TENUE)
                t.set_alpha(int(255 * a))
                sup.blit(t, (x, y + 7))
            y = y0 + 4 * 56 + 16
            t = _texto(f["normal"], "CONTROL", DORADO)
            sup.blit(t, (x0, y))
            for i, (boton, accion) in enumerate(mando):
                a = _salida_cubica((aparicion - 0.3 - i * 0.05) / 0.3)
                t1 = _texto(f["chico"], boton, BLANCO)
                t2 = _texto(f["texto"], accion, TENUE)
                t1.set_alpha(int(255 * a))
                t2.set_alpha(int(255 * a))
                sup.blit(t1, (x0 + 10 + i * 240, y + 38))
                sup.blit(t2, (x0 + 10 + i * 240, y + 62))

        self._abrir(Panel("AYUDA", (w, 540), [Boton("REGRESAR", lambda: self.cerrar_panel(),
                                                       ((w - 260) // 2, 462, 260, 54))], extra))

    def _tecla(self, sup, texto, x, y, f, alfa=1.0):
        # dibuja una tecla y devuelve donde termina
        t = _texto(f["tecla"], texto, (40, 26, 18))
        r = pygame.Rect(x, y, max(44, t.get_width() + 24), 40)
        cap = pygame.Surface((r.width, r.height + 4), pygame.SRCALPHA)
        pygame.draw.rect(cap, (120, 92, 60, int(255 * alfa)), (0, 4, r.width, r.height), border_radius=8)
        pygame.draw.rect(cap, (*DORADO, int(255 * alfa)), (0, 0, r.width, r.height), border_radius=8)
        t2 = t.copy()
        t2.set_alpha(int(255 * alfa))
        cap.blit(t2, t2.get_rect(center=(r.width // 2, r.height // 2)))
        sup.blit(cap, r.topleft)
        return r.right

    def abrir_creditos(self):
        w = 760
        secciones = [
            ("PROYECTO", ["Simulación de la Hacienda San Jacinto"]),
            ("INTEGRANTES", ["Hernández Roque Kyrsa Jolieth", "Mercado Ortega Vanessa de los Ángeles",
                             "Izaguirre Espinoza Alberth Hernán"]),
            ("AGRADECIMIENTOS", ["Modelo del caballo: evgeney24 (sketchfab.com/evgeney24)",
                                 "Jessua René Solís Juárez, contribuyente"]),
        ]

        def extra(sup, panel, f):
            y, n = 96, 0
            for titulo, lineas in secciones:
                for j, txt in enumerate([titulo] + lineas):
                    a = _salida_cubica((panel.tiempo - n * 0.06) / 0.35)
                    n += 1
                    t = _texto(f["normal"] if j == 0 else f["texto"], txt, DORADO if j == 0 else BLANCO)
                    t.set_alpha(int(255 * a))
                    sup.blit(t, t.get_rect(midtop=(panel.rect.width // 2, y + int((1 - a) * 14))))
                    y += 36 if j == 0 else 30
                y += 16

        self._abrir(Panel("CRÉDITOS", (w, 540), [Boton("REGRESAR", lambda: self.cerrar_panel(),
                                                          ((w - 260) // 2, 462, 260, 54))], extra))

    def confirmar_salida(self):
        # empieza en cancelar para no salir sin querer
        w = 560

        def extra(sup, panel, f):
            t = _texto(f["texto"], "¿Seguro que quieres salir del juego?", TENUE)
            sup.blit(t, t.get_rect(center=(w // 2, 120)))

        self._abrir(Panel("SALIR", (w, 250), [
            Boton("CANCELAR", lambda: self.cerrar_panel(), (40, 168, 220, 54)),
            Boton("SALIR", self.salir, (w - 260, 168, 220, 54)),
        ], extra))

    def salir(self):
        pygame.quit()
        sys.exit()

    # entrada
    def _mover_foco(self, paso):
        if self.panel:
            n = len(self.panel.widgets)
            self.panel.foco = (self.panel.foco + paso) % n
        else:
            self.foco = (self.foco + paso) % len(self.opciones)
        self.sonar("hover")

    def _lateral(self, direccion):
        # izquierda/derecha
        if self.panel:
            w = self.panel.widgets[self.panel.foco]
            if not w.ajustar(direccion, self) and len(self.panel.widgets) > 1 and isinstance(w, Boton):
                # si es un boton cambia al otro boton
                self._mover_foco(direccion)

    def _aceptar(self):
        if self.panel:
            self.panel.widgets[self.panel.foco].activar(self)
        else:
            self.sonar("click")
            self.opciones[self.foco][1]()

    def _atras(self):
        if self.panel:
            self.cerrar_panel()

    def _local(self, pos):
        if not self.panel:
            return pos
        return pos[0] - self.panel.rect.x, pos[1] - self._y_panel()

    def _y_panel(self):
        return self.panel.rect.y + int((1 - _salida_cubica(self.panel.anim)) * 40)

    def manejar_evento(self, e):
        # teclado, control y mouse
        if self.saliendo:
            return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self._mover_foco(-1)
            elif e.key in (pygame.K_DOWN, pygame.K_s, pygame.K_TAB):
                self._mover_foco(1)
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self._lateral(-1)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self._lateral(1)
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._aceptar()
            elif e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self._atras()
        elif e.type == pygame.JOYHATMOTION:
            hx, hy = e.value
            if hy:
                self._mover_foco(-hy)
            elif hx:
                self._lateral(hx)
        elif e.type == pygame.JOYAXISMOTION and e.axis in (0, 1):
            if abs(e.value) > 0.6 and self.t - self.ultimo_eje > 0.22:
                self.ultimo_eje = self.t
                if e.axis == 1:
                    self._mover_foco(1 if e.value > 0 else -1)
                else:
                    self._lateral(1 if e.value > 0 else -1)
        elif e.type == pygame.JOYBUTTONDOWN:
            if e.button == 0:
                self._aceptar()
            elif e.button == 1:
                self._atras()
        elif e.type == pygame.MOUSEMOTION:
            if self.arrastrando:
                self.arrastrando.desde_x(self._local(e.pos)[0])
            else:
                self._foco_raton(e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self._clic(e.pos)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if self.arrastrando:
                self.sonar("tick")
            self.arrastrando = None
        elif e.type == pygame.MOUSEWHEEL and self.panel:
            w = self.panel.widgets[self.panel.foco]
            if isinstance(w, (Deslizador, Selector)):
                w.ajustar(1 if e.y > 0 else -1, self)

    def _foco_raton(self, pos):
        if self.panel:
            local = self._local(pos)
            for i, w in enumerate(self.panel.widgets):
                if w.contiene(local) and i != self.panel.foco:
                    self.panel.foco = i
                    self.sonar("hover")
        else:
            for i, r in enumerate(self.rects):
                if r.inflate(40, 8).collidepoint(pos) and i != self.foco:
                    self.foco = i
                    self.sonar("hover")

    def _clic(self, pos):
        if self.panel:
            if self.panel.cerrando:
                return
            local = self._local(pos)
            for i, w in enumerate(self.panel.widgets):
                if not w.contiene(local):
                    continue
                self.panel.foco = i
                if isinstance(w, Deslizador):
                    self.arrastrando = w
                    if w.barra.inflate(30, 30).collidepoint(local):
                        w.desde_x(local[0])
                elif isinstance(w, Selector):
                    w.clic(local, self)
                else:
                    w.activar(self)
                return
        else:
            for i, r in enumerate(self.rects):
                if r.inflate(40, 8).collidepoint(pos):
                    self.foco = i
                    self._aceptar()
                    return

    # dibujo
    def actualizar(self, dt):
        self.t += dt
        if self.panel:
            p = self.panel
            p.tiempo += dt
            if p.cerrando:
                p.anim -= dt * 5
                if p.anim <= 0:
                    despues = p.al_cerrar
                    self.panel = None
                    if despues:
                        despues()
            else:
                p.anim = min(1.0, p.anim + dt * 4)
        if self.saliendo:
            self.saliendo = min(1.0, self.saliendo + dt * 1.6)
            if self.saliendo >= 1.0:
                self.start_game = True

    def dibujar(self, sup, dt):
        mx, my = pygame.mouse.get_pos()
        # fondo que se mueve despacio y con el mouse
        sobra_x = self.fondo.get_width() - ANCHO
        sobra_y = self.fondo.get_height() - ALTO
        px = sobra_x * (0.5 + 0.30 * math.sin(self.t * 0.07) - 0.12 * (mx / ANCHO - 0.5))
        py = sobra_y * (0.5 + 0.25 * math.cos(self.t * 0.05) - 0.12 * (my / ALTO - 0.5))
        sup.blit(self.fondo, (-int(px), -int(py)))
        sup.blit(self.sombra, (0, 0))
        self._dibujar_particulas(sup, dt, mx, my)

        intro = _salida_cubica(self.t / 1.1)
        self._dibujar_titulo(sup, intro)

        # botones (se oscurecen si hay un panel abierto)
        atenuar = _salida_cubica(self.panel.anim) if self.panel else 0.0
        for i, (texto, _, desc) in enumerate(self.opciones):
            a = _salida_cubica((self.t - 0.35 - i * 0.09) / 0.5)
            enfocado = (i == self.foco) and not self.panel
            self.brillos[i] = _acercar(self.brillos[i], 1.0 if enfocado else 0.0, dt, 12)
            b = self.brillos[i]
            r = self.rects[i].move(int(-80 * (1 - a)) + int(18 * b), 0)
            alfa = int(255 * a * (1 - 0.65 * atenuar))
            capa = pygame.Surface((r.width + 40, r.height), pygame.SRCALPHA)
            fondo = pygame.Rect(0, 0, r.width + int(24 * b), r.height)
            pygame.draw.rect(capa, (*_mezclar_color(MADERA, MADERA_CLARA, b), int(150 + 90 * b)), fondo, border_radius=12)
            pygame.draw.rect(capa, (*_mezclar_color((120, 100, 86), DORADO, b), 255), fondo, 2, border_radius=12)
            pygame.draw.rect(capa, (*DORADO, 255), (0, 8, int(6 + 4 * b), r.height - 16), border_radius=3)
            t = _texto(self.f["boton"], texto, _mezclar_color(TENUE, BLANCO, b))
            capa.blit(t, t.get_rect(midleft=(28 + int(10 * b), r.height // 2)))
            if b > 0.05:   # flechita
                fx = fondo.right - 30 + int(6 * math.sin(self.t * 6)) * (b > 0.9)
                cy = r.height // 2
                pygame.draw.polygon(capa, (*DORADO, int(255 * b)), [(fx, cy - 9), (fx + 11, cy), (fx, cy + 9)])
            capa.set_alpha(alfa)
            sup.blit(capa, r.topleft)

        # descripcion del boton seleccionado
        if not self.panel:
            desc = self.opciones[self.foco][2]
            t = _texto(self.f["texto"], desc, TENUE)
            t.set_alpha(int(255 * intro))
            sup.blit(t, (100, self.rects[-1].bottom + 34))

        self._dibujar_pie(sup, intro)

        if self.panel:
            self._dibujar_panel(sup, dt)

        if self.saliendo:
            negro = pygame.Surface((ANCHO, ALTO))
            negro.set_alpha(int(255 * self.saliendo))
            sup.blit(negro, (0, 0))
            t = _texto(self.f["subtitulo"], "Cargando la hacienda...", DORADO)
            t.set_alpha(int(255 * _limitar(self.saliendo * 2 - 0.6)))
            sup.blit(t, t.get_rect(center=(ANCHO // 2, ALTO // 2)))

    def _dibujar_titulo(self, sup, a):
        y = 74 + int((1 - a) * -24)
        sombra = _texto(self.f["titulo"], "HACIENDA", (0, 0, 0))
        titulo = _texto(self.f["titulo"], "HACIENDA", DORADO)
        for s, d in ((sombra, 4), (titulo, 0)):
            s.set_alpha(int(255 * a * (0.6 if d else 1)))
            sup.blit(s, (92 + d, y + d))
        sub = _texto(self.f["subtitulo"], "SAN JACINTO", BLANCO)
        sub.set_alpha(int(255 * a))
        sup.blit(sub, (98, y + 88))
        ancho_linea = int(330 * _salida_cubica((self.t - 0.4) / 0.8))
        pygame.draw.line(sup, DORADO, (98, y + 134), (98 + ancho_linea, y + 134), 2)
        fecha = _texto(self.f["fecha"], "Batalla de San Jacinto · 14 de septiembre de 1856", TENUE)
        fecha.set_alpha(int(255 * _salida_cubica((self.t - 0.6) / 0.8)))
        sup.blit(fecha, (98, y + 146))

    def _dibujar_pie(self, sup, a):
        if self.panel:
            ayuda = "↑↓ Elegir   ←→ Ajustar   Enter Aceptar   Esc Regresar"
        else:
            ayuda = "↑↓ Elegir   Enter Aceptar   Ratón o control también funcionan"
        t = _texto(self.f["chico"], ayuda, GRIS)
        t.set_alpha(int(220 * a))
        sup.blit(t, t.get_rect(bottomright=(ANCHO - 32, ALTO - 24)))
        conectado = self.control.JoyStick is not None
        txt = "Control conectado" if conectado else "Teclado y ratón"
        color = (150, 220, 140) if conectado else GRIS
        t = _texto(self.f["chico"], txt, color)
        t.set_alpha(int(220 * a))
        sup.blit(t, (56, ALTO - 24 - t.get_height()))
        pulso = 4 + int(1.5 * math.sin(self.t * 3)) if conectado else 4
        pygame.draw.circle(sup, color, (40, ALTO - 24 - t.get_height() // 2), pulso)

    def _dibujar_particulas(self, sup, dt, mx, my):
        if not hasattr(self, "_capa_particulas"):
            self._capa_particulas = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa = self._capa_particulas
        capa.fill((0, 0, 0, 0))
        for p in self.particulas:
            p[1] -= p[2] * dt
            p[0] += (p[5] + 6 * math.sin(self.t * 0.5 + p[4])) * dt
            if p[1] < -10:
                p[1], p[0] = ALTO + 10, random.uniform(0, ANCHO)
            brillo = 0.5 + 0.5 * math.sin(self.t * 1.7 + p[4])
            x = int(p[0] - (mx / ANCHO - 0.5) * 30 * p[3] / 3)
            y = int(p[1] - (my / ALTO - 0.5) * 20 * p[3] / 3)
            r = p[3]
            pygame.draw.circle(capa, (255, 214, 150, int(40 * brillo)), (x, y), int(r * 3))
            pygame.draw.circle(capa, (255, 236, 200, int(170 * brillo)), (x, y), max(1, int(r)))
        sup.blit(capa, (0, 0))

    def _dibujar_panel(self, sup, dt):
        p = self.panel
        a = _salida_cubica(p.anim)
        # fondo oscuro detras del panel
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((8, 5, 3, int(120 * a)))
        sup.blit(velo, (0, 0))

        capa = pygame.Surface(p.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(capa, (36, 25, 19, 236), capa.get_rect(), border_radius=18)
        pygame.draw.rect(capa, DORADO, capa.get_rect(), 2, border_radius=18)
        pygame.draw.rect(capa, (*DORADO, 60), capa.get_rect().inflate(-12, -12), 1, border_radius=14)
        t = _texto(self.f["panel"], p.titulo, DORADO)
        capa.blit(t, t.get_rect(midtop=(p.rect.width // 2, 24)))
        ancho = int(t.get_width() * _salida_cubica(p.tiempo / 0.5))
        pygame.draw.line(capa, DORADO, (p.rect.width // 2 - ancho // 2, 72), (p.rect.width // 2 + ancho // 2, 72), 2)
        if p.dibujar_extra:
            p.dibujar_extra(capa, p, self.f)
        for i, w in enumerate(p.widgets):
            w.dibujar(capa, i == p.foco, dt, self.f)
        capa.set_alpha(int(255 * a))
        sup.blit(capa, (p.rect.x, self._y_panel()))


def mostrar_menu(control: Joycon.Joycon, sensibilidad_inicial=1.0, sonido_inicial=5, velocidad_inicial=2.0):
    # loop del menu, devuelve la configuracion al darle iniciar
    pygame.init()
    try:
        pygame.mixer.init()
    except pygame.error as e:
        print(f"⚠️ Audio no disponible: {e}")

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Hacienda San Jacinto - Menú")
    reloj = pygame.time.Clock()

    musica = Audios.Musica()
    musica.cargar_musica("menu", "indian-pacific-271.mp3")
    musica.reproducir_musica("menu", bucle=True)
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(sonido_inicial / 10.0)

    sonido = sonido_inicial if isinstance(sonido_inicial, (int, float)) else 5
    menu = Menu(control=control, sensibilidad=sensibilidad_inicial, sonido=sonido, velocidad=velocidad_inicial)

    while not menu.start_game:
        dt = min(reloj.tick(60) / 1000.0, 0.05)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.JOYDEVICEADDED:
                control.__init__(control.ZonaMuerta, control.Sensi, 0, control.IDV)
            elif evento.type == pygame.JOYDEVICEREMOVED:
                control.desactivar()
            menu.manejar_evento(evento)

        menu.actualizar(dt)
        menu.dibujar(pantalla, dt)
        pygame.display.flip()

    musica.detener_musica()
    pygame.quit()

    return {
        "Configuracion": (menu.valores["sensibilidad"], menu.valores["velocidad"]),
        "Volumen": menu.valores["volumen"],
        "SiempreDia": menu.siempre_dia,
        "ControlConfiguracion": control,
    }
