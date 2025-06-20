import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np

import Clases.Camara as Camara
import Clases.Util as Util
import Clases.Joycon as Joycon
from Escenas import EscenaClass as Escenas, skybox
from Escenas import Hacienda as Hac
from Escenas import Menu as menu
from Audio.Sonido import sonido
import Escenas.Iluminacion as iluminacion


def main():
    # Inicializar controles
    pygame.joystick.init()
    Control = Joycon.Joycon(0.3, 4, 0)
    resultados = menu.mostrar_menu(Control)

    sensibilidad = resultados["Configuracion"][0]
    velocidad = resultados["Configuracion"][1]
    control_configurado = resultados["ControlConfiguracion"]

    Control = control_configurado
    
    
    pygame.init()
    glutInit()
    # Ahora inicia la escena 3D
    pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
    gluPerspective(45, (800 / 600), 0.1, 700.0)
    ...
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Proyecto")

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (display[0] / display[1]), 0.1, 700.0)
    glMatrixMode(GL_MODELVIEW)

    sonido.cargar_efecto("Efecto_paso","footstep.mp3")

    # Cámara
    camara = Camara.Camaras([0.0, 3.0, 20.0], 0.0, 0.0, velocidad, sensibilidad, [0.0, 1.0, 0.0])
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    # Escenas
    
    Hacienda = Escenas.Escenas(Hac.ListHacienda)
    Hacienda.cargar()
    SkyBoxes = skybox.Skybox(250)
    
    #iluminacion
   
    iluminacion.init_lighting()

    clock = pygame.time.Clock()
    running = True

    # Variables para ciclo día/noche
    esDia = False
    ultima_hora = -1

    # Sonido
    sonido.reproducir_musica("musica1", True)

    
    while running:
        dt = clock.tick(60)

        tiempo_segundos = dt / 1000.0
        camara.velocidad = 10 * tiempo_segundos

        # Simulación del tiempo: cada 5 segundos = 1 hora
        segundos = pygame.time.get_ticks() / 1000
        horas = int((segundos % 120) // 0.5)

        # Cambio de estado día/noche solo si cambia la hora
        """if horas != ultima_hora:
            ultima_hora = horas
            if horas == 6:
                esDia = True
            elif horas == 18:
                esDia = False"""

        keys = pygame.key.get_pressed()

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[K_ESCAPE]:
                running = False
            if event.type == pygame.JOYDEVICEADDED:
                Control.__init__(Control.ZonaMuerta, Control.Sensi, 0, Control.IDV)
            if event.type == pygame.JOYDEVICEREMOVED:
                Control.desactivar()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True
        # Movimiento del mouse
        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        camara.cam_yaw += mouse_dx * camara.sensibilidad
        camara.cam_pitch -= mouse_dy * camara.sensibilidad

        r = Util.normalizar(Util.cross(camara.cam_target, camara.up))
    
      # Movimiento teclado
        if keys[K_w]:
            nueva_pos = [camara.cam_pos[i] + camara.cam_target[i] * camara.velocidad for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos):
                camara.cam_pos = nueva_pos
        if keys[K_s]:
            nueva_pos = [camara.cam_pos[i] - camara.cam_target[i] * camara.velocidad for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos):
                camara.cam_pos = nueva_pos
        if keys[K_a]:
            nueva_pos = [camara.cam_pos[i] - r[i] * camara.velocidad for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos):
                camara.cam_pos = nueva_pos
        if keys[K_d]:
            nueva_pos = [camara.cam_pos[i] + r[i] * camara.velocidad for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos):
                camara.cam_pos = nueva_pos


        # Movimiento por joystick
        if Control.JoyStick is not None:
            izq = Control.get_PalancaIzquierda()
            der = Control.get_PalancaDerecha()

            nueva_pos = [camara.cam_pos[i] + camara.cam_target[i] * (-Control.IDV * izq[1]) for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos):
                camara.cam_pos = nueva_pos

            nueva_pos = [camara.cam_pos[i] + r[i] * (Control.IDV * izq[0]) for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos):
                camara.cam_pos = nueva_pos

            camara.cam_yaw += der[0] * Control.Sensi
            camara.cam_pitch -= der[1] * Control.Sensi


        camara.cam_pitch = max(-89.0, min(89.0, camara.cam_pitch))
        camara.ActualizarTarget()
        camara.cam_target = Util.normalizar(camara.cam_target)

        # Render
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        gluLookAt(
            camara.cam_pos[0], camara.cam_pos[1], camara.cam_pos[2],
            camara.cam_pos[0] + camara.cam_target[0],
            camara.cam_pos[1] + camara.cam_target[1],
            camara.cam_pos[2] + camara.cam_target[2],
            0, 1, 0
        )

        # Dibujar Skybox según hora
        SkyBoxes.draw(True)

        #Iluminacion
        iluminacion.update_light()
        
        iluminacion.draw_light_source(3)
      
        # Dibujar escena
        Hacienda.DibujarEscena()

        # Mostrar en pantalla
        pygame.display.flip()

    pygame.joystick.quit()
    sonido.cerrar_sonidos() 
    pygame.quit()

if __name__ == "__main__":
    main()