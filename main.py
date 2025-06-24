import sys
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import glutInit
import numpy as np

import Clases.Camara as Camara
import Clases.Util as Util
import Clases.Joycon as Joycon
from Escenas import EscenaClass as Escenas, skybox
from Escenas import Hacienda as Hac
from Escenas import Menu as menu
from Audio.Sonido import sonido
import Escenas.Iluminacion as iluminacion


def init_opengl(width, height):
    # Ajusta el viewport a toda la ventana
    glViewport(0, 0, width, height)
    # Configura la proyección con aspecto dinámico
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(
        45.0,            # campo de visión
        width / height,  # relación de aspecto dinámica
        0.1,             # plano cercano
        700.0            # plano lejano
    )
    # Vuelve al modelview
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    # Habilita depth test
    glEnable(GL_DEPTH_TEST)


def main():
    # Inicializar controles
    pygame.joystick.init()
    Control = Joycon.Joycon(0.3, 4, 0)
    resultados = menu.mostrar_menu(Control)

    sensibilidad = resultados["Configuracion"][0]
    velocidad = resultados["Configuracion"][1]
    control_configurado = resultados["ControlConfiguracion"]

    Control = control_configurado

    # Inicializar Pygame y OpenGL
    pygame.init()
    glutInit()

    # Obtener resolución de la pantalla y permitir redimensionar
    info = pygame.display.Info()
    ancho, alto = info.current_w, info.current_h
    display = (ancho, alto)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption("Proyecto")

    # Inicializar OpenGL con dimensiones actuales
    init_opengl(ancho, alto)

    # Carga de sonidos
    sonido.cargar_efecto("Efecto_paso", "footstep.mp3")

    # Configurar cámara
    camara = Camara.Camaras([0.0, 3.0, 20.0], 0.0, 0.0, velocidad, sensibilidad, [0.0, 1.0, 0.0])
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    # Cargar escenas
    Hacienda = Escenas.Escenas(Hac.ListHacienda)
    Hacienda.cargar()
    SkyBoxes = skybox.Skybox(250)

    # Iluminación
    iluminacion.init_lighting()

    clock = pygame.time.Clock()
    running = True

    # Reproducir música de fondo
    # Variables para ciclo día/noche
    esDia = False
    ultima_hora = -1

    # Sonido
  
    sonido.reproducir_musica("musica1", True)

    while running:
        # Control de tiempo
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
            if event.type == QUIT or pygame.key.get_pressed()[K_ESCAPE]:
                running = False

            # Manejo de redimensionamiento
            elif event.type == VIDEORESIZE:
                ancho, alto = event.w, event.h
                display = (ancho, alto)
                pygame.display.set_mode(display, DOUBLEBUF | OPENGL | RESIZABLE)
                init_opengl(ancho, alto)

            # Reconexión de joystick
            elif event.type == pygame.JOYDEVICEADDED:
                Control.__init__(Control.ZonaMuerta, Control.Sensi, 0, Control.IDV)
            elif event.type == pygame.JOYDEVICEREMOVED:
                Control.desactivar()

        # Movimiento del mouse
        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        camara.cam_yaw   += mouse_dx * camara.sensibilidad
        camara.cam_pitch -= mouse_dy * camara.sensibilidad

        # Calcular vector lateral
        r = Util.normalizar(Util.cross(camara.cam_target, camara.up))

        # Movimiento con teclado
        if keys[K_w]:
            nueva_pos = [camara.cam_pos[i] + camara.cam_target[i] * camara.velocidad for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos) and not SkyBoxes.collides(nueva_pos):
                camara.cam_pos = nueva_pos
        if keys[K_s]:
            nueva_pos = [camara.cam_pos[i] - camara.cam_target[i] * camara.velocidad for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos) and not SkyBoxes.collides(nueva_pos):
                camara.cam_pos = nueva_pos
        if keys[K_a]:
            nueva_pos = [camara.cam_pos[i] - r[i] * camara.velocidad for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos) and not SkyBoxes.collides(nueva_pos):
                camara.cam_pos = nueva_pos
        if keys[K_d]:
            nueva_pos = [camara.cam_pos[i] + r[i] * camara.velocidad for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos) and not SkyBoxes.collides(nueva_pos):
                camara.cam_pos = nueva_pos
        # Nuevos controles: subir y bajar cámara
        if keys[K_SPACE]:
            # Mover cámara hacia arriba
            nueva_pos = camara.cam_pos.copy()
            nueva_pos[1] += camara.velocidad
            if not Hacienda.Modelos[0].collides(nueva_pos) and not SkyBoxes.collides(nueva_pos):
                camara.cam_pos = nueva_pos
        if keys[K_LSHIFT] or keys[K_RSHIFT]:
            # Mover cámara hacia abajo
            nueva_pos = camara.cam_pos.copy()
            nueva_pos[1] -= camara.velocidad
            if not Hacienda.Modelos[0].collides(nueva_pos) and not SkyBoxes.collides(nueva_pos):
                camara.cam_pos = nueva_pos

        # Movimiento con joystick
        if Control.JoyStick is not None:
            izq = Control.get_PalancaIzquierda()
            der = Control.get_PalancaDerecha()

            nueva_pos = [camara.cam_pos[i] + camara.cam_target[i] * (-Control.IDV * izq[1]) for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos) and not SkyBoxes.collides(nueva_pos):
                camara.cam_pos = nueva_pos

            nueva_pos = [camara.cam_pos[i] + r[i] * (Control.IDV * izq[0]) for i in range(3)]
            if not Hacienda.Modelos[0].collides(nueva_pos) and not SkyBoxes.collides(nueva_pos):
                camara.cam_pos = nueva_pos
            camara.cam_yaw  += der[0] * Control.Sensi
            camara.cam_pitch -= der[1] * Control.Sensi

        # Limitar pitch
        camara.cam_pitch = max(-89.0, min(89.0, camara.cam_pitch))
        camara.ActualizarTarget()
        camara.cam_target = Util.normalizar(camara.cam_target)

        # Renderizado
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        gluLookAt(
            camara.cam_pos[0], camara.cam_pos[1], camara.cam_pos[2],
            camara.cam_pos[0] + camara.cam_target[0],
            camara.cam_pos[1] + camara.cam_target[1],
            camara.cam_pos[2] + camara.cam_target[2],
            0, 1, 0
        )

        # Dibujar skybox (como en el código original)
        SkyBoxes.draw(True)

        # Iluminación
        iluminacion.update_light()

        iluminacion.draw_light_source(3)

        # Dibujar escena
        Hacienda.DibujarEscena()

        # Actualizar pantalla
        pygame.display.flip()

    # Limpieza
    pygame.joystick.quit()
    sonido.cerrar_sonidos()
    pygame.quit()


if __name__ == "__main__":
    main()
