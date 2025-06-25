import os
import pygame
from pygame.locals import *
from Clases import Modelo

# Ruta base dinámica
import sys
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Construcción de rutas para modelos
def modelo_path(*relative_path):
    return os.path.join(BASE_PATH, *relative_path)

Hacienda = Modelo.Modelos(
    modelo_path("modelosObj", "Hacienda", "Hacienda.obj"),
    modelo_path("modelosObj", "Hacienda", "Hacienda.mtl"),
    modelo_path("modelosObj", "colision_combined.obj")
)

Mesa = Modelo.Modelos(
    modelo_path("modelosObj", "Mesas", "Mesas.obj"),
    modelo_path("modelosObj", "Mesas", "Mesas.mtl"),
    modelo_path("modelosObj", "colision_combined.obj")
)

Armas = Modelo.Modelos(
    modelo_path("modelosObj", "Pistolas", "Guns2.obj"),
    modelo_path("modelosObj", "Pistolas", "Guns2.mtl"),
    modelo_path("modelosObj", "colision_combined.obj")
)

Caballo = Modelo.Modelos(
    modelo_path("modelosObj", "Caballos", "Horse.obj"),
    modelo_path("modelosObj", "Caballos", "Horse.mtl"),
    modelo_path("modelosObj", "colision_combined.obj")
)

Retrato = Modelo.Modelos(
    modelo_path("modelosObj", "Retratos", "Marcofotos.obj"),
    modelo_path("modelosObj", "Retratos", "Marcofotos.mtl"),
    modelo_path("modelosObj", "colision_combined.obj")
)

ListHacienda = [Hacienda, Mesa, Armas, Caballo, Retrato]
