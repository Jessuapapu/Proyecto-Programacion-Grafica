import pygame
import sys
import os
from Clases import Joycon, Botones, Sliders, Paneles
from Audio import Audios  # <-- Importar controlador de audio


# Resolución base y escalado
INTERNAL_WIDTH, INTERNAL_HEIGHT = 704, 384
SCALE = 2
WINDOW_WIDTH, WINDOW_HEIGHT = INTERNAL_WIDTH * SCALE, INTERNAL_HEIGHT * SCALE

# Superficie base y ventana
internal_surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Menú Mejorado Pixel Perfect")
clock = pygame.time.Clock()

# Fuente
font = pygame.font.SysFont("Consolas", 15, bold=True)

# Fondo
background_img = pygame.image.load("Recursos/Imagenes/imagen.jpg").convert()
background_img = pygame.transform.scale(background_img, (INTERNAL_WIDTH, INTERNAL_HEIGHT))


class SettingsPanel:
    def __init__(self, sliders, back_button, close_callback, control: Joycon.Joycon):
        self.sliders = sliders  # Diccionario solo con sliders
        self.back_button = back_button  # Botón "REGRESAR"
        self.close_callback = close_callback
        self.control = control
        self.rect = pygame.Rect((INTERNAL_WIDTH - 500) // 2, (INTERNAL_HEIGHT - 300) // 2, 500, 300)

    def draw(self, surface, mouse_pos, click):
        pygame.draw.rect(surface, (103, 77, 64), self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)

        # Dibujar sliders
        for slider in self.sliders.values():
            slider.draw(surface, mouse_pos, click)

        # Dibujar botón REGRESAR
        if self.back_button:
            self.back_button.draw(surface, mouse_pos, click, (103, 77, 64), (133, 107, 94))

        control_text = (
            f"CONTROL: {self.control.JoyStick.get_name()}"
            if self.control.JoyStick else "CONTROL: NO CONECTADO"
        )
        text = font.render(control_text, True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.rect.centerx, 250 - 15))
        surface.blit(text, text_rect)

        pygame.mixer.music.set_volume(self.sliders["sonido"].value / 3)
       

        if click:
            mouse_rect = pygame.Rect(mouse_pos[0] // SCALE, mouse_pos[1] // SCALE, 1, 1)
            if not self.rect.contains(mouse_rect):
                self.close_callback()


class Menu:
    def __init__(self, control, sensibilidad, sonido, velocidad):
        self.start_game = False
        self.active_panel = None
        self.control = control

        # Guardar valores simples
        self.sonido = sonido
        self.sensibilidad = sensibilidad
        self.velocidad = velocidad

        # Crear sliders
        self.slider_sonido = Sliders.Slider("sonido", "SONIDO", (300, 70), 0, 3, 1, self.sonido)
        self.slider_sensibilidad = Sliders.Slider("sensibilidad", "SENSIBILIDAD", (300, 130), 0.0, 2.0, 0.1, self.sensibilidad)
        self.slider_velocidad = Sliders.Slider("velocidad", "VELOCIDAD", (300, 180), 1,150, 1, self.velocidad)

        self.sliders = {
            "sonido": self.slider_sonido,
            "sensibilidad": self.slider_sensibilidad,
            "velocidad": self.slider_velocidad
        }

        # Botón regresar separado
        self.regresar_button = Botones.Button("REGRESAR", (300, 250), self.clear_panel, 150, 30)

        # Botones del menú principal
        self.buttons = [
            Botones.Button("INICIO", (60, 60), self.start),
            Botones.Button("CONFIGURACION", (60, 120), self.toggle_settings),
            Botones.Button("CREDITOS", (60, 180), self.show_credits),
            Botones.Button("AYUDA", (60, 240), self.show_help),
            Botones.Button("SALIR", (60, 300), self.exit_game)
        ]

    def start(self):
        self.start_game = True

    def toggle_settings(self):
        self.control.JoyStick = pygame.joystick.Joystick(0) if pygame.joystick.get_count() > 0 else None
        # Pasa sliders y botón regresar por separado
        self.active_panel = SettingsPanel(self.sliders, self.regresar_button, self.clear_panel, self.control)

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def show_credits(self):
        self.active_panel = Paneles.Panel([
            "Proyecto de semestre: Simulación de la Hacienda San Jacinto",
            "Integrantes: Solis Juarez Jessua Rene",
            "- Hernandez Roque Kyrsa Jolieth",
            "- Mercado Ortega Vanessa de los Angeles",
            "- Izaguirre Espinoza Alberth Hernan",
            "Grupo: 3T1-COMS",
            "Creditos especiales:",
            "Horse C.por: evgeney24 (https://sketchfab.com/evgeney24)",
            "REGRESAR"
        ], self.clear_panel)

    def show_help(self):
        self.active_panel = Paneles.Panel([
            "Controles del teclado:",
            "W - Mover hacia arriba",
            "S - Mover hacia abajo",
            "A - Mover a la izquierda",
            "D - Mover a la derecha",
            "Joystick izquierdo - Movimiento",
            "Joystick derecho - Cámara",
            "shift - baja , Espacio - Sube",
            "REGRESAR"
        ], self.clear_panel)

    def clear_panel(self):
        self.active_panel = None

    def draw(self, mouse_pos, click):
        internal_surface.blit(background_img, (0, 0))

        if self.active_panel:
            self.active_panel.draw(internal_surface, mouse_pos, click)
        else:
            for btn in self.buttons:
                btn.draw(internal_surface, mouse_pos, click, (103, 77, 64), (133, 107, 94))


def mostrar_menu(control: Joycon.Joycon, sensibilidad_inicial=1.0, sonido_inicial=True, velocidad_inicial=2.0):
    pygame.init()
    pygame.mixer.init()  # Inicializa mixer explícitamente

    # Música del menú
    musica = Audios.Musica()
    ruta_musica = "Recursos/Sonidos/indian-pacific-271.mp3"
    if not os.path.exists(ruta_musica):
        print(f"ERROR: No se encontró la música en {ruta_musica}")
    else:
        print(f" Música encontrada: {ruta_musica}")
        musica.cargar_musica("menu", "indian-pacific-271.mp3")  # Se usa solo el nombre aquí
        musica.reproducir_musica("menu", bucle=True)
        pygame.mixer.music.set_volume(1.0)

    # Configuración inicial
    sensibilidad = sensibilidad_inicial
    sonido = 3 if sonido_inicial else 0
    velocidad = velocidad_inicial

    menu = Menu(control=control, sensibilidad=sensibilidad, sonido=sonido, velocidad=velocidad)
    running = True

    while running:
        if menu.start_game:
            break

        mouse_pos = pygame.mouse.get_pos()
        click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.JOYDEVICEADDED:
                control.__init__(control.ZonaMuerta, control.Sensi, 0, control.IDV)
            if event.type == pygame.JOYDEVICEREMOVED:
                control.desactivar()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        # Ajustar volumen con slider
        pygame.mixer.music.set_volume(menu.slider_sonido.value / 3)

        # Dibujar menú
        menu.draw(mouse_pos, click)
        scaled_surface = pygame.transform.scale(internal_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    # Detener música antes de salir al juego
    musica.detener_musica()
    pygame.quit()

    return {
        "Configuracion": (menu.slider_sensibilidad.value, menu.slider_velocidad.value),
        "ControlConfiguracion": control
    }