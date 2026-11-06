# ventana de opengl que comparten el menu y el juego
# asi al darle iniciar no se cierra y se vuelve a abrir
# la pantalla completa se cambia con la ventana de SDL para no perder el contexto de opengl
import warnings

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, RESIZABLE

TAM_VENTANA = (1408, 768)       # tamaño en modo ventana

pantalla_completa = False
_ventana_sdl = None


def _sdl():
    # objeto Window de SDL de la ventana actual (pygame-ce)
    global _ventana_sdl
    if _ventana_sdl is None:
        for crear in (lambda: pygame.Window.from_display_module(),
                      lambda: __import__("pygame._sdl2.video", fromlist=["Window"]).Window.from_display_module()):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")    # avisa que es obsoleto pero sigue funcionando
                    _ventana_sdl = crear()
                break
            except Exception:
                pass
    return _ventana_sdl


_tam_normal = TAM_VENTANA


def crear(completa=False, titulo="Hacienda San Jacinto"):
    # se llama una sola vez al iniciar
    global _tam_normal
    info = pygame.display.Info()
    w = min(TAM_VENTANA[0], int(info.current_w * 0.9))
    h = min(TAM_VENTANA[1], int(info.current_h * 0.85))
    _tam_normal = (w, h)
    pygame.display.set_mode((w, h), DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption(titulo)
    if completa:
        poner_pantalla_completa(True)
    return tamano()


def tamano():
    try:
        return pygame.display.get_window_size()
    except Exception:
        return pygame.display.get_surface().get_size()


def poner_pantalla_completa(activar):
    # cambia entre ventana y pantalla completa sin cerrar la ventana
    global pantalla_completa
    if activar == pantalla_completa:
        return tamano()
    win = _sdl()
    try:
        if win is not None:
            if activar:
                win.set_fullscreen(True)       # True = a la resolucion del escritorio
            else:
                win.set_windowed()
                win.size = _tam_normal
                try:
                    win.position = pygame.WINDOWPOS_CENTERED
                except Exception:
                    pass
        else:
            pygame.display.toggle_fullscreen()
        pantalla_completa = activar
    except Exception as e:
        print(f"No se pudo cambiar a pantalla completa: {e}")
    pygame.event.pump()
    return tamano()


def alternar():
    return poner_pantalla_completa(not pantalla_completa)
