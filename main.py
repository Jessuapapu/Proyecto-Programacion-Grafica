# Hacienda San Jacinto - archivo principal
# primero sale el menu y despues se abre la ventana de opengl con la escena
import os
import sys
import subprocess


def verificar_dependencias():
    # instala lo que falte con el mismo python que corre el juego
    # (si no, pip lo instala en otra version y da error de modulo)
    if getattr(sys, 'frozen', False):   # el .exe ya trae todo
        return
    import importlib
    import importlib.util
    import importlib.metadata as metadata

    faltantes = [m for m in ("pygame", "OpenGL", "numpy", "PIL") if importlib.util.find_spec(m) is None]
    if not faltantes:
        return

    print(f"Faltan librerías ({', '.join(faltantes)}). Instalando con {sys.executable} ...")
    requisitos = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    python = [sys.executable, "-m"]

    if subprocess.call(python + ["pip", "--version"]) != 0:
        subprocess.check_call(python + ["ensurepip", "--upgrade"])

    # pygame y pygame-ce chocan porque los dos usan la carpeta pygame
    try:
        metadata.distribution("pygame")
        subprocess.call(python + ["pip", "uninstall", "-y", "pygame"])
    except metadata.PackageNotFoundError:
        pass

    subprocess.check_call(python + ["pip", "install", "-r", requisitos])
    importlib.invalidate_caches()
    print("Librerías instaladas correctamente.\n")


verificar_dependencias()

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import Clases.Camara as Camara
import Clases.Util as Util
import Clases.Joycon as Joycon
from Escenas import EscenaClass as Escenas, skybox
from Escenas.Nubes import Nubes
from Escenas import Hacienda as Hac
from Escenas import Menu as menu
from Escenas import Pausa
from Audio.Sonido import sonido
import Escenas.Iluminacion as iluminacion

# cuanto avanza la camara por cada punto de velocidad del menu
FACTOR_VELOCIDAD = 5.0
VELOCIDAD_GIRO_CIELO = 0.4    # grados por segundo que gira el cielo


# proyeccion en perspectiva segun el tamaño de la ventana
def init_opengl(width, height):
    height = max(1, height)  # por si la ventana se minimiza
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(
        45.0,            # fov
        width / height,
        0.1,
        700.0            # hasta donde se ve
    )
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glEnable(GL_DEPTH_TEST)


# la camara siempre queda a esta altura sobre el suelo
ALTURA_MINIMA_SUELO = 2.0


def mover(camara, escena, skybox_, nueva_pos):
    # solo mueve la camara si no choca con la casa, los arboles, el museo o el borde del mapa
    suelo = Hac.Terreno.altura_en(nueva_pos[0], nueva_pos[2]) + ALTURA_MINIMA_SUELO
    if nueva_pos[1] < suelo:
        nueva_pos = [nueva_pos[0], suelo, nueva_pos[2]]
    if (not escena.Modelos[0].collides(nueva_pos) and not Hac.Bosque.collides(nueva_pos)
            and not Hac.Museo.collides(nueva_pos)
            and not skybox_.collides(nueva_pos)):
        camara.cam_pos = nueva_pos


def capturar_raton(activo):
    # en el juego el mouse queda atrapado, en la pausa se suelta
    pygame.event.set_grab(activo)
    pygame.mouse.set_visible(not activo)
    pygame.mouse.get_rel()  # limpia el movimiento acumulado


# boton start del control
BOTON_PAUSA_JOYSTICK = 7


def mover_camara(camara, Control, Hacienda, SkyBoxes):
    # mouse, teclado y control
    keys = pygame.key.get_pressed()

    # mouse
    mouse_dx, mouse_dy = pygame.mouse.get_rel()
    camara.cam_yaw += mouse_dx * camara.sensibilidad
    camara.cam_pitch -= mouse_dy * camara.sensibilidad

    # vector hacia la derecha de la camara
    r = Util.normalizar(Util.cross(camara.cam_target, camara.up))
    v = camara.velocidad

    # teclado
    if keys[K_w]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[i] + camara.cam_target[i] * v for i in range(3)])
    if keys[K_s]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[i] - camara.cam_target[i] * v for i in range(3)])
    if keys[K_a]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[i] - r[i] * v for i in range(3)])
    if keys[K_d]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[i] + r[i] * v for i in range(3)])
    # subir / bajar
    if keys[K_SPACE]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[0], camara.cam_pos[1] + v, camara.cam_pos[2]])
    if keys[K_LSHIFT] or keys[K_RSHIFT]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[0], camara.cam_pos[1] - v, camara.cam_pos[2]])

    # control
    if Control.JoyStick is not None:
        try:
            izq = Control.get_PalancaIzquierda()
            der = Control.get_PalancaDerecha()
        except pygame.error:
            izq, der = [0, 0], [0, 0]
            Control.desactivar()

        mover(camara, Hacienda, SkyBoxes,
              [camara.cam_pos[i] + camara.cam_target[i] * (-Control.IDV * izq[1]) * v for i in range(3)])
        mover(camara, Hacienda, SkyBoxes,
              [camara.cam_pos[i] + r[i] * (Control.IDV * izq[0]) * v for i in range(3)])
        camara.cam_yaw += der[0] * Control.Sensi
        camara.cam_pitch -= der[1] * Control.Sensi

    # para que no se de vuelta la camara
    camara.cam_pitch = max(-89.0, min(89.0, camara.cam_pitch))
    camara.ActualizarTarget()
    camara.cam_target = Util.normalizar(camara.cam_target)


def main():
    # zona muerta, sensibilidad, numero de control
    pygame.joystick.init()
    Control = Joycon.Joycon(0.3, 4, 0)
    resultados = menu.mostrar_menu(Control)

    sensibilidad = resultados["Configuracion"][0]
    velocidad = resultados["Configuracion"][1]
    volumen = resultados.get("Volumen", 5)
    siempre_dia = resultados.get("SiempreDia", False)
    Control = resultados["ControlConfiguracion"]

    # pygame + opengl
    # no usamos glut porque en windows daba error con glutInit
    pygame.init()

    # el menu cierra pygame asi que hay que volver a abrir el control
    Control.__init__(Control.ZonaMuerta, Control.Sensi, 0, Control.IDV)

    # pantalla completa con la resolucion del monitor
    info = pygame.display.Info()
    ancho, alto = info.current_w, info.current_h
    pygame.display.set_mode((ancho, alto), DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption("Hacienda San Jacinto")

    init_opengl(ancho, alto)

    # sonidos
    sonido.cargar_efecto("Efecto_paso", "footstep.mp3")

    # camara
    # empieza frente al corredor
    camara = Camara.Camaras([0.0, 3.0, 45.0], 0.0, 0.0, velocidad, sensibilidad, [0.0, 1.0, 0.0])
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    # cargar modelos
    Hacienda = Escenas.Escenas(Hac.ListHacienda)
    Hacienda.cargar()
    SkyBoxes = skybox.Skybox(250)
    nubes = Nubes()

    # luces
    iluminacion.init_lighting()

    clock = pygame.time.Clock()
    running = True

    # musica con el volumen del menu
    sonido.reproducir_musica("musica1", True)
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(volumen / 10.0)

    pausa = Pausa.MenuPausa(volumen, sensibilidad, velocidad, siempre_dia)
    tiempo_juego = 0.0      # no avanza en pausa ni en modo siempre de dia
    if siempre_dia:
        tiempo_juego = iluminacion.segundos_para_hora(iluminacion.HORA_SIEMPRE_DIA)
    tiempo_nubes = 0.0      # las nubes si se mueven en siempre de dia
    pygame.mouse.get_rel()  # lo que se movio el mouse mientras cargaba

    def pausar():
        pausa.abrir()
        capturar_raton(False)

    def reanudar():
        pausa.cerrar()
        capturar_raton(True)

    while running:
        dt = clock.tick(60) / 1000.0
        if not pausa.abierto and not pausa.siempre_dia:
            tiempo_juego += dt
        if not pausa.abierto:
            tiempo_nubes += dt
        camara.velocidad = velocidad * FACTOR_VELOCIDAD * dt

        # ciclo dia/noche, 5 segundos = 1 hora
        # en siempre de dia la hora se queda fija
        if pausa.siempre_dia:
            tiempo_juego = iluminacion.segundos_para_hora(iluminacion.HORA_SIEMPRE_DIA)
        hora = iluminacion.hora_simulada(tiempo_juego)

        # eventos
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            # ESC abre o cierra la pausa
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                if not pausa.abierto:
                    pausar()
                elif pausa.atras():
                    reanudar()
            elif event.type == pygame.JOYBUTTONDOWN and event.button == BOTON_PAUSA_JOYSTICK:
                if pausa.abierto:
                    reanudar()
                else:
                    pausar()

            # si se hace alt+tab se pausa
            elif event.type == pygame.WINDOWFOCUSLOST and not pausa.abierto:
                pausar()

            # mouse dentro del menu de pausa
            elif pausa.abierto and event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION):
                accion = pausa.manejar_evento(event)
                if accion == "continuar":
                    reanudar()
                elif accion == "salir":
                    running = False

            # al cambiar el tamaño solo se ajusta el viewport
            # (volver a llamar set_mode borra las texturas)
            elif event.type == VIDEORESIZE:
                ancho, alto = event.w, event.h
                init_opengl(ancho, alto)

            # control conectado / desconectado
            elif event.type == pygame.JOYDEVICEADDED:
                Control.__init__(Control.ZonaMuerta, Control.Sensi, 0, Control.IDV)
            elif event.type == pygame.JOYDEVICEREMOVED:
                Control.desactivar()

        # valores de la configuracion de la pausa
        velocidad = pausa.valores["velocidad"]
        camara.sensibilidad = pausa.valores["sensibilidad"]
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(pausa.valores["volumen"] / 10.0)

        if not pausa.abierto:
            mover_camara(camara, Control, Hacienda, SkyBoxes)

        # dibujar
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        gluLookAt(
            camara.cam_pos[0], camara.cam_pos[1], camara.cam_pos[2],
            camara.cam_pos[0] + camara.cam_target[0],
            camara.cam_pos[1] + camara.cam_target[1],
            camara.cam_pos[2] + camara.cam_target[2],
            0, 1, 0
        )

        # luces despues de gluLookAt para que queden fijas
        iluminacion.update_light(hora)

        # cielo, sol y luna
        SkyBoxes.draw(iluminacion.estado['factor_dia'], iluminacion.estado['tinte_cielo'], camara.cam_pos,
                      giro=tiempo_nubes * VELOCIDAD_GIRO_CIELO)
        iluminacion.draw_light_source(camara.cam_pos)
        # nubes
        nubes.dibujar(tiempo_nubes, camara.cam_pos, iluminacion.estado)

        # escena
        iluminacion.activar_shader()
        Hacienda.DibujarEscena()
        iluminacion.desactivar_shader()

        # pausa encima de todo
        if pausa.abierto:
            pausa.dibujar(ancho, alto, hora)

        pygame.display.flip()

    # liberar memoria antes de cerrar
    Hacienda.liberar()
    nubes.liberar()
    pausa.liberar()
    pygame.joystick.quit()
    sonido.cerrar_sonidos()
    pygame.quit()


if __name__ == "__main__":
    main()
