import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# se carga los modelos de clases para una mejor estructura
import Modelos
import Camara

def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Modo caminar con gluLookAt")

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (display[0] / display[1]), 0.1, 700.0)
    glMatrixMode(GL_MODELVIEW)

    modelo = Modelos.Modelo('modelosObj/Hacienda.obj')
    camara = Camara.Camaras([0.0, 1.0, -100.0], 0.0 , 0.54 , 2.0)
    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick(120)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            """if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_presses = pygame.mouse.get_pressed()
                if mouse_presses[0]:
                    print("Left Mouse key was clicked" ) """   
                
        keys = pygame.key.get_pressed()
        
        
        if keys[K_d]:  # Avanzar
            camara.cam_pos[0] += 0.5 * camara.velocidad
        if keys[K_a]:
            camara.cam_pos[0] += -0.5 * camara.velocidad 
        if keys[K_w]:
            camara.cam_pos[2] += -0.5 * camara.velocidad 
        if keys[K_s]:
            camara.cam_pos[2] += 0.5 * camara.velocidad 
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        camara.InicializarTarget()

        # Definir la vista (cámara)
        gluLookAt(
            camara.cam_pos[0], camara.cam_pos[1], camara.cam_pos[2],
            camara.cam_target[0], camara.cam_target[1], camara.cam_target[2], 
            0, 1, 0                                
        )

        modelo.DibujarModelo()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
