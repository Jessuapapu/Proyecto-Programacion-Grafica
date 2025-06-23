from Clases import Modelo
import pygame
from pygame.locals import *



Hacienda = Modelo.Modelos("modelosObj/Hacienda/Hacienda.obj", "modelosObj/Hacienda/Hacienda.mtl", "modelosObj/Hacienda/Hacienda_colision.obj")
Mesa = Modelo.Modelos("modelosObj/Mesas/Mesas.obj","modelosObj/Mesas/Mesas.mtl")
Armas = Modelo.Modelos("modelosObj/Pistolas/Guns2.obj","modelosObj/Pistolas/Guns2.mtl")
Caballo = Modelo.Modelos("modelosObj/Caballos/Horse.obj","modelosObj/Caballos/Horse.mtl")
Retrato = Modelo.Modelos("modelosObj/Retratos/Marcofotos.obj","modelosObj/Retratos/Marcofotos.mtl")

ListHacienda = [Hacienda,Mesa,Armas,Caballo,Retrato]