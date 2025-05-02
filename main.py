import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# se carga las librerias que funcionan para cargar y guadar los modelos
import Modelos
import Camara

def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Modo caminar con gluLookAt")

    glEnable(GL_DEPTH_TEST)
    gluPerspective(45, (display[0] / display[1]), 0.1, 700.0)

    modelo = Modelos.Modelo('modelosObj/Hacienda.obj')
    camara = Camara.Camaras([0.0, 1.0, -250.0], 0.0 , 1, 2.0)
    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_presses = pygame.mouse.get_pressed()
                if mouse_presses[0]:
                    print("Left Mouse key was clicked" )    


        keys = pygame.key.get_pressed()


        # Rotaciones
        if keys[K_LEFT]:
            camara.cam_yaw -= camara.sencibilidad
        if keys[K_RIGHT]:
            camara.cam_yaw += camara.sencibilidad

        # Movimiento adelante / atrás
        sin_yaw = math.sin(math.radians(camara.cam_yaw))
        cos_yaw = math.cos(math.radians(camara.cam_yaw))

        if keys[K_w]:  # Avanzar
            camara.cam_pos[0] += sin_yaw * camara.velocidad
            camara.cam_pos[2] -= cos_yaw * camara.velocidad
            print(camara.cam_pos)
        if keys[K_s]:  # Retroceder
            camara.cam_pos[0] -= sin_yaw * camara.velocidad
            camara.cam_pos[2] += cos_yaw * camara.velocidad
            print(camara.cam_pos)
        if keys[K_a]:  # Izquierda
            camara.cam_pos[0] -= cos_yaw * camara.velocidad
            camara.cam_pos[2] -= sin_yaw * camara.velocidad
            print(camara.cam_pos)
        if keys[K_d]:  # Derecha
            camara.cam_pos[0] += cos_yaw * camara.velocidad
            camara.cam_pos[2] += sin_yaw * camara.velocidad
            print(camara.cam_pos)
            
        
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
