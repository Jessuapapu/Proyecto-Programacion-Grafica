from datetime import datetime
from OpenGL.GL import *
from OpenGL.GLU import *

# configurable parameters
CUBE_Y         = 100.0          # Altura del foco
DAY_INTENS     = 10.0          # Mucho más brillo en el día
NIGHT_INTENS   = 1.0           # Luz tenue en la noche
DAY_START_HR   = 6
DAY_END_HR     = 18
FADE_SPEED     = 0.1           # Transición más rápida

# Posición fija del foco: w=1.0 → luz puntual
light_pos = [0.0, CUBE_Y, 0.0, 1.0]
current_intensity = DAY_INTENS


def is_daytime() -> bool:
    hr = datetime.now().hour
    return DAY_START_HR <= hr < DAY_END_HR


def update_light():
    global current_intensity
    # Transición suave, pero hacia un día muy brillante
    target = DAY_INTENS if is_daytime() else NIGHT_INTENS
    current_intensity += (target - current_intensity) * FADE_SPEED

    # posición y color de la luz
    glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [current_intensity]*3 + [1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [current_intensity]*3 + [1.0])

    # Atenuación mínima para que la luz alcance lejos
    glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION,  1.0)
    glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION,    0.005)
    glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.0005)


def init_lighting():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glShadeModel(GL_SMOOTH)

    # Luz ambiental fuerte para “rellenar” sombras
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
    # Material base
    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.7, 0.7, 0.7, 1.0])


def draw_manual_cube(size=1.0):
    half = size / 2.0
    verts = [
        [ half,  half, -half], [ half, -half, -half],
        [-half, -half, -half], [-half,  half, -half],
        [ half,  half,  half], [ half, -half,  half],
        [-half, -half,  half], [-half,  half,  half]
    ]
    faces = [
        (0,1,2,3), (3,2,6,7),
        (1,5,6,2), (4,5,1,0),
        (4,0,3,7), (5,4,7,6)
    ]
    glBegin(GL_QUADS)
    for f in faces:
        for idx in f:
            glVertex3fv(verts[idx])
    glEnd()


def draw_light_source(size=0.5):
    glPushMatrix()
    glTranslatef(light_pos[0], light_pos[1], light_pos[2])
    # Emisión para que el cubo se vea como foco brillante
    glMaterialfv(GL_FRONT, GL_EMISSION, [current_intensity]*3 + [1.0])
    draw_manual_cube(size)
    # Reset emisión
    glMaterialfv(GL_FRONT, GL_EMISSION, [0.2, 0.2, 0.2, 1.0])
    glPopMatrix()