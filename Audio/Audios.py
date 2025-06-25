import pygame
from pygame import mixer
import os
import sys

# Ruta base dinámica compatible con PyInstaller
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

class Musica:
    def __init__(self, ruta_relativa="Recursos/Sonidos"):
        if not pygame.mixer.get_init():
            mixer.init()
        self.musicas = {}
        self.efectos = {}

        # Ruta absoluta a los sonidos
        self.ruta_base = os.path.join(BASE_PATH, ruta_relativa)

    def cargar_musica(self, nombre, archivo):
        ruta = os.path.join(self.ruta_base, archivo)
        if os.path.isfile(ruta):
            self.musicas[nombre] = ruta

    def cargar_efecto(self, nombre, archivo):
        ruta = os.path.join(self.ruta_base, archivo)
        if os.path.isfile(ruta):
            self.efectos[nombre] = mixer.Sound(ruta)

    def reproducir_efecto(self, nombre):
        if nombre in self.efectos:
            self.efectos[nombre].play()

    def reproducir_musica(self, nombre, bucle=True):
        if nombre in self.musicas:
            mixer.music.load(self.musicas[nombre])
            mixer.music.play(-1 if bucle else 0)

    def detener_musica(self):
        mixer.music.stop()

    def pausar_musica(self):
        mixer.music.pause()

    def continuar_musica(self):
        mixer.music.unpause()

    def cerrar_sonidos(self):
        pygame.mixer.stop()
