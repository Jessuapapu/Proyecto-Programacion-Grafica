import pygame
from pygame import mixer
import os
import sys

# Ruta base dinámica compatible con PyInstaller.
# Debe apuntar a la raíz del proyecto (antes apuntaba a la carpeta Audio/ y
# por eso la música y los efectos del juego nunca se encontraban).
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _mixer_listo():
    """Inicializa el mezclador si hace falta. Devuelve False si no hay dispositivo de audio."""
    if mixer.get_init():
        return True
    try:
        mixer.init()
        return True
    except pygame.error as e:
        print(f"⚠️ Audio no disponible: {e}")
        return False


class Musica:
    def __init__(self, ruta_relativa=os.path.join("Recursos", "Sonidos")):
        self.musicas = {}
        self.efectos = {}
        self._efectos_pendientes = {}

        # Ruta absoluta a los sonidos
        self.ruta_base = os.path.join(BASE_PATH, ruta_relativa)

    def cargar_musica(self, nombre, archivo):
        ruta = os.path.join(self.ruta_base, archivo)
        if os.path.isfile(ruta):
            self.musicas[nombre] = ruta
        else:
            print(f"⚠️ No se encontró la música: {ruta}")

    def cargar_efecto(self, nombre, archivo):
        ruta = os.path.join(self.ruta_base, archivo)
        if not os.path.isfile(ruta):
            print(f"⚠️ No se encontró el efecto: {ruta}")
            return
        if _mixer_listo():
            self.efectos[nombre] = mixer.Sound(ruta)

    def reproducir_efecto(self, nombre):
        if nombre in self.efectos and mixer.get_init():
            self.efectos[nombre].play()

    def reproducir_musica(self, nombre, bucle=True):
        if nombre in self.musicas and _mixer_listo():
            mixer.music.load(self.musicas[nombre])
            mixer.music.play(-1 if bucle else 0)

    def detener_musica(self):
        if mixer.get_init():
            mixer.music.stop()

    def pausar_musica(self):
        if mixer.get_init():
            mixer.music.pause()

    def continuar_musica(self):
        if mixer.get_init():
            mixer.music.unpause()

    def cerrar_sonidos(self):
        if mixer.get_init():
            mixer.stop()
