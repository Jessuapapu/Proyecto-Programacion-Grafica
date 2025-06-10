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


def draw_manual_cube(size=1.0):
    half = size / 2.0
    vertices = [
        [ half,  half, -half],
        [ half, -half, -half],
        [-half, -half, -half],
        [-half,  half, -half],
        [ half,  half,  half],
        [ half, -half,  half],
        [-half, -half,  half],
        [-half,  half,  half]
    ]

    faces = [
        (0, 1, 2, 3),
        (3, 2, 6, 7),
        (1, 5, 6, 2),
        (4, 5, 1, 0),
        (4, 0, 3, 7),
        (5, 4, 7, 6)
    ]

    glBegin(GL_QUADS)
    for face in faces:
        for vertex in face:
            glVertex3fv(vertices[vertex])
    glEnd()


    
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    update_light()
    draw_manual_cube()
    glutSwapBuffers()

def idle():
    glutPostRedisplay()

def reshape(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(width)/float(height), 1.0, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0, 5, 20, 0, 0, 0, 0, 1, 0)
