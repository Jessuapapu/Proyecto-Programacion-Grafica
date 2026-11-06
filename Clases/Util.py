import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# funciones para vectores

def normalizar(vec):
    l = math.sqrt(sum([x ** 2 for x in vec]))
    return [x / l for x in vec]

def cross(a, b):
    # producto cruz
    return [
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0]
    ]