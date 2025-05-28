import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import Clases.Camara as Camara, Clases.Util as Util, Clases.Joycon as Joycon
from Escenas import EscenaClass as Escenas, skybox
from Escenas import Hacienda as Hac
from Audio.Sonido import sonido


def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Proyecto")

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (display[0] / display[1]), 0.1, 700.0)
    glMatrixMode(GL_MODELVIEW)
    
    
    #Inicializar controles
    pygame.joystick.init()
    Control = Joycon.Joycon(0.3,4,0)
           
           
    # posición inicial y configuración
    camara = Camara.Camaras([0.0, 3.0, 20.0], 0.0, 0.0, 0.1, 1.0, [0.0, 1.0, 0.0])
    pygame.event.set_grab(True)        # captura el mouse en la ventana
    pygame.mouse.set_visible(False)    # oculta el cursor


    clock = pygame.time.Clock()
    running = True
    
    # Escenas
    Hacienda = Escenas.Escenas(Hac.ListHacienda)
    SkyBoxes = skybox.Skybox(250)
    # Sonido
    sonido.reproducir_musica("Paseo")

    
    while running:
        dt = clock.tick(60)
        tiempo_segundos = dt / 1000.0
        camara.velocidad = 10 * tiempo_segundos
        
        keys = pygame.key.get_pressed()
        

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[K_ESCAPE]:
                running = False
                # Handle hotplugging
            if event.type == pygame.JOYDEVICEADDED:
                # Carga las confifuraciones del control
                Control.__init__(Control.ZonaMuerta,Control.Sensi,0,Control.IDV)
                
            if event.type == pygame.JOYDEVICEREMOVED:
                Control.desactivar()


        # Movimiento del mouse
        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        camara.cam_yaw += mouse_dx * camara.sensibilidad
        camara.cam_pitch -= mouse_dy * camara.sensibilidad

     
        r = Util.normalizar(Util.cross(camara.cam_target, camara.up))
        
        if keys[K_w]:
            camara.cam_pos = [camara.cam_pos[i] + camara.cam_target[i] * camara.velocidad for i in range(3)]
        if keys[K_s]:
            camara.cam_pos = [camara.cam_pos[i] - camara.cam_target[i] * camara.velocidad for i in range(3)]
        if keys[K_a]:
            camara.cam_pos = [camara.cam_pos[i] - r[i] * camara.velocidad for i in range(3)]
        if keys[K_d]:
            camara.cam_pos = [camara.cam_pos[i] + r[i] * camara.velocidad for i in range(3)]
   
        # Movimiento de la camara en el plano (Palanca Izquierda)
        if Control.JoyStick is not None:
            camara.cam_pos = [camara.cam_pos[i] + camara.cam_target[i] * (((-1*Control.IDV) * Control.get_PalancaIzquierda()[1])) for i in range(3)]
            
            camara.cam_pos = [camara.cam_pos[i] + r[i] * (Control.get_PalancaIzquierda()[0] * Control.IDV ) for i in range(3)]
        
        # Movimiento de la vista de la camara con el control (Palanca Derecha)
        if Control.JoyStick is not None:
            camara.cam_yaw += Control.get_PalancaDerecha()[0] * Control.Sensi
            camara.cam_pitch -= Control.get_PalancaDerecha()[1] * Control.Sensi

        
        camara.cam_pitch = max(-89.0, min(89.0, camara.cam_pitch))
        camara.ActualizarTarget()
        camara.cam_target = Util.normalizar(camara.cam_target)
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        gluLookAt(
            camara.cam_pos[0], camara.cam_pos[1], camara.cam_pos[2],
            camara.cam_pos[0] + camara.cam_target[0],
            camara.cam_pos[1] + camara.cam_target[1],
            camara.cam_pos[2] + camara.cam_target[2],
            0, 1, 0
        )
        
        """
        Como hace falta hacer las escenas donde va todo esto, alberth se va encargar de colocar las cosas en su lugar y hacer las escenas por 
        medio de clases, luego yo me voy encargar en poner la iluminacion
        """
        
        # modelo.DibujarModelo()
        SkyBoxes.draw()
        Hacienda.DibujarEscena()
        pygame.display.flip()
        
    pygame.joystick.quit()
    sonido.detener_musica()
    pygame.quit()

if __name__ == "__main__":
    main()
