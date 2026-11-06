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
from Clases import Ventana, Colision
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


def mover(camara, mundo, delta):
    # mueve la camara: se resbala por paredes y objetos en vez de quedarse pegada
    # y nunca queda debajo del suelo
    destino = [camara.cam_pos[i] + delta[i] for i in range(3)]
    suelo = Hac.Terreno.altura_en(destino[0], destino[2]) + ALTURA_MINIMA_SUELO
    destino[1] = max(destino[1], suelo)
    p = mundo.mover(camara.cam_pos, destino)
    p[1] = max(p[1], Hac.Terreno.altura_en(p[0], p[2]) + ALTURA_MINIMA_SUELO)
    camara.cam_pos = p


def capturar_raton(activo):
    # en el juego el mouse queda atrapado, en la pausa se suelta
    pygame.event.set_grab(activo)
    pygame.mouse.set_visible(not activo)
    pygame.mouse.get_rel()  # limpia el movimiento acumulado


# boton start del control
BOTON_PAUSA_JOYSTICK = 7


def mover_camara(camara, Control, mundo):
    # mouse, teclado y control
    keys = pygame.key.get_pressed()

    # mouse
    mouse_dx, mouse_dy = pygame.mouse.get_rel()
    camara.cam_yaw += mouse_dx * camara.sensibilidad
    camara.cam_pitch -= mouse_dy * camara.sensibilidad

    # vector hacia la derecha de la camara
    r = Util.normalizar(Util.cross(camara.cam_target, camara.up))
    t = camara.cam_target
    v = camara.velocidad

    # se suma todo el movimiento del frame y se mueve una sola vez
    adelante, lado, arriba = 0.0, 0.0, 0.0
    if keys[K_w]:
        adelante += 1
    if keys[K_s]:
        adelante -= 1
    if keys[K_a]:
        lado -= 1
    if keys[K_d]:
        lado += 1
    # subir / bajar
    if keys[K_SPACE]:
        arriba += 1
    if keys[K_LSHIFT] or keys[K_RSHIFT]:
        arriba -= 1

    # control
    if Control.JoyStick is not None:
        try:
            izq = Control.get_PalancaIzquierda()
            der = Control.get_PalancaDerecha()
        except pygame.error:
            izq, der = [0, 0], [0, 0]
            Control.desactivar()
        adelante += -Control.IDV * izq[1]
        lado += Control.IDV * izq[0]
        camara.cam_yaw += der[0] * Control.Sensi
        camara.cam_pitch -= der[1] * Control.Sensi

    if adelante or lado or arriba:
        delta = [(t[i] * adelante + r[i] * lado) * v for i in range(3)]
        delta[1] += arriba * v
        mover(camara, mundo, delta)

    # para que no se de vuelta la camara
    camara.cam_pitch = max(-89.0, min(89.0, camara.cam_pitch))
    camara.ActualizarTarget()
    camara.cam_target = Util.normalizar(camara.cam_target)


def cargar_escena():
    # se carga una sola vez, al volver al menu se queda en memoria
    sonido.cargar_efecto("Efecto_paso", "footstep.mp3")
    hacienda = Escenas.Escenas(Hac.ListHacienda)
    hacienda.cargar()
    sky = skybox.Skybox(250)
    # colisiones: casa, cercas, caballos y muebles (malla) + troncos, pedestales y vitrinas
    malla = Colision.MallaColision.desde_obj(Hac.modelo_path("modelosObj", "colision_hacienda.obj"))
    mundo = Colision.Mundo(malla, [Hac.Bosque, Hac.Museo], limite=sky.size - 0.5)
    escena = {"hacienda": hacienda, "skybox": sky, "nubes": Nubes(), "mundo": mundo}
    iluminacion.init_lighting()
    return escena


def jugar(escena, Control, config):
    # loop del juego, devuelve "menu" o "salir"
    Hacienda, SkyBoxes, nubes = escena["hacienda"], escena["skybox"], escena["nubes"]
    sensibilidad, velocidad = config["sensibilidad"], config["velocidad"]

    ancho, alto = Ventana.tamano()
    init_opengl(ancho, alto)
    iluminacion.init_lighting(usar_shader=False)

    # camara, empieza frente al corredor
    camara = Camara.Camaras([0.0, 3.0, 45.0], 0.0, 0.0, velocidad, sensibilidad, [0.0, 1.0, 0.0])
    capturar_raton(True)

    clock = pygame.time.Clock()
    resultado = None

    # musica con el volumen del menu
    sonido.reproducir_musica("musica1", True)
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(config["volumen"] / 10.0)

    pausa = Pausa.MenuPausa(config["volumen"], sensibilidad, velocidad, config["siempre_dia"])
    tiempo_juego = 0.0      # no avanza en pausa ni en modo siempre de dia
    if pausa.siempre_dia:
        tiempo_juego = iluminacion.segundos_para_hora(iluminacion.HORA_SIEMPRE_DIA)
    tiempo_nubes = 0.0      # las nubes si se mueven en siempre de dia
    pygame.mouse.get_rel()  # lo que se movio el mouse mientras cargaba

    def pausar():
        pausa.abrir()
        capturar_raton(False)

    def reanudar():
        pausa.cerrar()
        capturar_raton(True)

    while resultado is None:
        dt = clock.tick(60) / 1000.0
        if not pausa.abierto and not pausa.siempre_dia:
            tiempo_juego += dt
        if not pausa.abierto:
            tiempo_nubes += dt
        camara.velocidad = velocidad * FACTOR_VELOCIDAD * dt

        # ciclo dia/noche, 7.5 segundos = 1 hora (3 minutos el dia completo)
        # en siempre de dia la hora se queda fija
        if pausa.siempre_dia:
            tiempo_juego = iluminacion.segundos_para_hora(iluminacion.HORA_SIEMPRE_DIA)
        hora = iluminacion.hora_simulada(tiempo_juego)

        # eventos
        for event in pygame.event.get():
            if event.type == QUIT:
                resultado = "salir"

            # F11 pantalla completa
            elif event.type == KEYDOWN and event.key == K_F11:
                Ventana.alternar()

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

            # control conectado / desconectado
            elif event.type == pygame.JOYDEVICEADDED:
                Control.__init__(Control.ZonaMuerta, Control.Sensi, 0, Control.IDV)
            elif event.type == pygame.JOYDEVICEREMOVED:
                Control.desactivar()

            # mouse, teclado y control dentro del menu de pausa
            elif pausa.abierto:
                accion = pausa.manejar_evento(event)
                if accion == "continuar":
                    reanudar()
                elif accion in ("menu", "salir"):
                    resultado = accion

        # si cambio el tamaño de la ventana (o pantalla completa) se ajusta el viewport
        # (no se llama set_mode porque borra las texturas)
        if Ventana.tamano() != (ancho, alto):
            ancho, alto = Ventana.tamano()
            init_opengl(ancho, alto)

        # valores de la configuracion de la pausa
        velocidad = pausa.valores["velocidad"]
        camara.sensibilidad = pausa.valores["sensibilidad"]
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(pausa.valores["volumen"] / 10.0)

        if not pausa.abierto:
            mover_camara(camara, Control, escena["mundo"])

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
            pausa.dibujar(ancho, alto, hora, dt)

        pygame.display.flip()

    # lo que se cambio en la pausa se guarda para el menu
    config["volumen"] = pausa.valores["volumen"]
    config["sensibilidad"] = pausa.valores["sensibilidad"]
    config["velocidad"] = pausa.valores["velocidad"]
    config["siempre_dia"] = pausa.siempre_dia
    pausa.liberar()
    sonido.detener_musica()
    capturar_raton(False)
    return resultado


def main():
    # una sola ventana para el menu y el juego
    pygame.init()
    pygame.joystick.init()
    Ventana.crear(completa=False)
    Control = Joycon.Joycon(0.3, 4, 0)    # zona muerta, sensibilidad, numero de control

    config = {"sensibilidad": 1.0, "velocidad": 2.0, "volumen": 5, "siempre_dia": False}
    escena = None

    while True:
        resultados = menu.mostrar_menu(Control, config["sensibilidad"], config["volumen"],
                                       config["velocidad"], config["siempre_dia"])
        config["sensibilidad"], config["velocidad"] = resultados["Configuracion"]
        config["volumen"] = resultados.get("Volumen", 5)
        config["siempre_dia"] = resultados.get("SiempreDia", False)
        Control = resultados["ControlConfiguracion"]

        if escena is None:
            escena = cargar_escena()
        if jugar(escena, Control, config) == "salir":
            break

    # liberar memoria antes de cerrar
    escena["hacienda"].liberar()
    escena["nubes"].liberar()
    pygame.joystick.quit()
    sonido.cerrar_sonidos()
    pygame.quit()


if __name__ == "__main__":
    main()
