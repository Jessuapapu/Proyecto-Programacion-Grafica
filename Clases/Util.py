import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# se carga los modelos de clases para una mejor estructura
import Modelos
import Clases.Camara as Camara

def normalizar(vec):
    l = math.sqrt(sum([x ** 2 for x in vec]))
    return [x / l for x in vec]

def cross(a, b):
    return [
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0]
    ]