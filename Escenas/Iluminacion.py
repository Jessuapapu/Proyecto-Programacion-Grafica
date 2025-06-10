from datetime import datetime
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# -------------------- configurable parameters 
CUBE_Y      = 5.0
DAY_INTENS  = 1.0
NIGHT_INTENS = 0.2
DAY_START_HR = 6
DAY_END_HR   = 18
FADE_SPEED   = 0.05

current_intensity = DAY_INTENS


def is_daytime() -> bool:
    hour = datetime.now().hour
    return DAY_START_HR <= hour < DAY_END_HR


def update_light():
    global current_intensity
    target = DAY_INTENS if is_daytime() else NIGHT_INTENS
    current_intensity += (target - current_intensity) * FADE_SPEED

    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [current_intensity]*3 + [1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [current_intensity]*3 + [1.0])
    glMaterialfv(GL_FRONT, GL_EMISSION, [current_intensity]*3 + [1.0])


def init_lighting():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glShadeModel(GL_SMOOTH)

    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, CUBE_Y, 0.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.05, 0.05, 0.05, 1.0])
    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.4, 0.4, 0.4, 1.0])


def draw_cube_light():
    glPushMatrix()
    glTranslatef(0.0, CUBE_Y, -10.0)
    glutSolidCube(1.0)
    glPopMatrix()


def draw_ground():
    glPushMatrix()
    glTranslatef(0.0, -0.51, -10.0)
    size = 20
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-size, 0, -size)
    glVertex3f(size, 0, -size)
    glVertex3f(size, 0, size)
    glVertex3f(-size, 0, size)
    glEnd()
    glPopMatrix()
