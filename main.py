import os
import sys
import subprocess


def verificar_dependencias():
    """Instala las librerías que falten usando el MISMO Python que ejecuta el juego.
    Así se evita el error "No module named 'pygame'" cuando pip instaló los
    paquetes en otra versión de Python."""
    if getattr(sys, 'frozen', False):   # el .exe ya trae todo incluido
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

    # El pygame original choca con pygame-ce (ambos se instalan en la carpeta "pygame")
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
from Escenas import Hacienda as Hac
from Escenas import Menu as menu
from Escenas import Pausa
from Audio.Sonido import sonido
import Escenas.Iluminacion as iluminacion

# Unidades por segundo que avanza la cámara por cada punto del slider "VELOCIDAD"
FACTOR_VELOCIDAD = 5.0


# Para la normalizacion de la camara
def init_opengl(width, height):
    height = max(1, height)  # evita división por cero al minimizar
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


# Altura mínima de la cámara sobre el suelo (al caminar sobre lomas la cámara sube sola)
ALTURA_MINIMA_SUELO = 2.0


def mover(camara, escena, skybox_, nueva_pos):
    """Mueve la cámara solo si la nueva posición no choca con la hacienda, con un
    árbol ni sale del skybox. Nunca deja que la cámara quede bajo el terreno."""
    suelo = Hac.Terreno.altura_en(nueva_pos[0], nueva_pos[2]) + ALTURA_MINIMA_SUELO
    if nueva_pos[1] < suelo:
        nueva_pos = [nueva_pos[0], suelo, nueva_pos[2]]
    if (not escena.Modelos[0].collides(nueva_pos) and not Hac.Bosque.collides(nueva_pos)
            and not Hac.Museo.collides(nueva_pos)
            and not skybox_.collides(nueva_pos)):
        camara.cam_pos = nueva_pos


def capturar_raton(activo):
    """En el juego el ratón queda atrapado e invisible; en la pausa se libera."""
    pygame.event.set_grab(activo)
    pygame.mouse.set_visible(not activo)
    pygame.mouse.get_rel()  # descarta el movimiento acumulado


# Botón "Start" / "Menu" del control (Xbox en SDL2) para pausar
BOTON_PAUSA_JOYSTICK = 7


def mover_camara(camara, Control, Hacienda, SkyBoxes):
    """Movimiento con ratón, teclado y joystick (solo cuando el juego no está en pausa)."""
    keys = pygame.key.get_pressed()

    # Movimiento del mouse
    mouse_dx, mouse_dy = pygame.mouse.get_rel()
    camara.cam_yaw += mouse_dx * camara.sensibilidad
    camara.cam_pitch -= mouse_dy * camara.sensibilidad

    # Calcular vector lateral
    r = Util.normalizar(Util.cross(camara.cam_target, camara.up))
    v = camara.velocidad

    # Movimiento con teclado
    if keys[K_w]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[i] + camara.cam_target[i] * v for i in range(3)])
    if keys[K_s]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[i] - camara.cam_target[i] * v for i in range(3)])
    if keys[K_a]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[i] - r[i] * v for i in range(3)])
    if keys[K_d]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[i] + r[i] * v for i in range(3)])
    # Subir y bajar cámara
    if keys[K_SPACE]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[0], camara.cam_pos[1] + v, camara.cam_pos[2]])
    if keys[K_LSHIFT] or keys[K_RSHIFT]:
        mover(camara, Hacienda, SkyBoxes, [camara.cam_pos[0], camara.cam_pos[1] - v, camara.cam_pos[2]])

    # Movimiento con joystick (escalado por el tiempo de cuadro)
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

    # Limitar pitch
    camara.cam_pitch = max(-89.0, min(89.0, camara.cam_pitch))
    camara.ActualizarTarget()
    camara.cam_target = Util.normalizar(camara.cam_target)


def main():
    # Inicializar controles
    pygame.joystick.init()
    Control = Joycon.Joycon(0.3, 4, 0)
    resultados = menu.mostrar_menu(Control)

    sensibilidad = resultados["Configuracion"][0]
    velocidad = resultados["Configuracion"][1]
    volumen = resultados.get("Volumen", 5)
    siempre_dia = resultados.get("SiempreDia", False)
    Control = resultados["ControlConfiguracion"]

    # Inicializar Pygame y OpenGL
    # (no se usa GLUT: glutInit() fallaba en Windows porque PyOpenGL no incluye freeglut)
    pygame.init()

    # El menú cierra pygame al terminar: los joysticks abiertos antes quedan inválidos
    Control.__init__(Control.ZonaMuerta, Control.Sensi, 0, Control.IDV)

    # Obtener resolución de la pantalla y permitir redimensionar
    info = pygame.display.Info()
    ancho, alto = info.current_w, info.current_h
    pygame.display.set_mode((ancho, alto), DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption("Hacienda San Jacinto")

    # Inicializar OpenGL con dimensiones actuales
    init_opengl(ancho, alto)

    # Carga de sonidos
    sonido.cargar_efecto("Efecto_paso", "footstep.mp3")

    # Configurar cámara
    # Posición inicial frente al corredor de la hacienda (antes empezaba pegada a una pared)
    camara = Camara.Camaras([0.0, 3.0, 45.0], 0.0, 0.0, velocidad, sensibilidad, [0.0, 1.0, 0.0])
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

    # Música de fondo con el volumen elegido en el menú
    sonido.reproducir_musica("musica1", True)
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(volumen / 10.0)

    pausa = Pausa.MenuPausa(volumen, sensibilidad, velocidad, siempre_dia)
    tiempo_juego = 0.0      # segundos de juego (no avanza durante la pausa ni en "siempre de día")
    if siempre_dia:
        tiempo_juego = iluminacion.segundos_para_hora(iluminacion.HORA_SIEMPRE_DIA)
    pygame.mouse.get_rel()  # descarta el movimiento acumulado durante la carga

    def pausar():
        pausa.abrir()
        capturar_raton(False)

    def reanudar():
        pausa.cerrar()
        capturar_raton(True)

    while running:
        # Control de tiempo
        dt = clock.tick(60) / 1000.0
        if not pausa.abierto and not pausa.siempre_dia:
            tiempo_juego += dt
        camara.velocidad = velocidad * FACTOR_VELOCIDAD * dt

        # Ciclo día/noche continuo (cada 5 segundos = 1 hora simulada); se congela en la pausa.
        # En modo "siempre de día" la hora queda fija; al volver al ciclo continúa desde ahí.
        if pausa.siempre_dia:
            tiempo_juego = iluminacion.segundos_para_hora(iluminacion.HORA_SIEMPRE_DIA)
        hora = iluminacion.hora_simulada(tiempo_juego)

        # Eventos
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            # ESC abre / cierra el menú de pausa (ya no cierra el programa)
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

            # Si la ventana pierde el foco (Alt+Tab) el juego se pausa solo
            elif event.type == pygame.WINDOWFOCUSLOST and not pausa.abierto:
                pausar()

            # Clics y arrastres dentro del menú de pausa
            elif pausa.abierto and event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION):
                accion = pausa.manejar_evento(event)
                if accion == "continuar":
                    reanudar()
                elif accion == "salir":
                    running = False

            # Manejo de redimensionamiento: en pygame 2 no hace falta volver a llamar
            # set_mode (hacerlo puede destruir el contexto OpenGL y las texturas)
            elif event.type == VIDEORESIZE:
                ancho, alto = event.w, event.h
                init_opengl(ancho, alto)

            # Reconexión de joystick
            elif event.type == pygame.JOYDEVICEADDED:
                Control.__init__(Control.ZonaMuerta, Control.Sensi, 0, Control.IDV)
            elif event.type == pygame.JOYDEVICEREMOVED:
                Control.desactivar()

        # Valores cambiados en la configuración de la pausa
        velocidad = pausa.valores["velocidad"]
        camara.sensibilidad = pausa.valores["sensibilidad"]
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(pausa.valores["volumen"] / 10.0)

        if not pausa.abierto:
            mover_camara(camara, Control, Hacienda, SkyBoxes)

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

        # Iluminación (después de gluLookAt para que las luces queden fijas en el mundo)
        iluminacion.update_light(hora)

        # Cielo: mezcla suave entre día y noche + sol/luna (centrado en la cámara)
        SkyBoxes.draw(iluminacion.estado['factor_dia'], iluminacion.estado['tinte_cielo'], camara.cam_pos)
        iluminacion.draw_light_source(camara.cam_pos)

        # Dibujar escena
        iluminacion.activar_shader()
        Hacienda.DibujarEscena()
        iluminacion.desactivar_shader()

        # Menú de pausa encima de la escena congelada
        if pausa.abierto:
            pausa.dibujar(ancho, alto, hora)

        # Actualizar pantalla
        pygame.display.flip()

    # Limpieza (los buffers se liberan mientras el contexto OpenGL sigue activo)
    Hacienda.liberar()
    pausa.liberar()
    pygame.joystick.quit()
    sonido.cerrar_sonidos()
    pygame.quit()


if __name__ == "__main__":
    main()
