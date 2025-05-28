import pygame
from pygame import mixer
import os

class Musica:
    def __init__(self, ruta_base="Recursos\Sonidos"):
        if not pygame.mixer.get_init():
            mixer.init()
        self.musicas = {}
        self.ruta_base = ruta_base
        self.efectos={}

#Carga la musica de fondo para el paseo
    def cargar_musica(self, nombre, archivo):
        ruta = os.path.join(self.ruta_base, archivo)
        if os.path.isfile(ruta):
            self.musicas[nombre] = ruta

#Carga los efectos de sonido
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

#Detiene la musica completamente, es decir la musica de fondo    
    def detener_musica(self):
     mixer.music.stop()
     self.musica_actual = None
   
    def pausar_musica(self):
     mixer.music.pause()

    def continuar_musica(self):
        mixer.music.unpause()

    def cerrar_sonidos(self):
        pygame.mixer.stop()


