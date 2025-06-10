import pygame
import sys
from PIL import  Image #Librería para procesamiento de imágenes (no usada directamente aquí, pero útil si se desea)#
pygame.init()

# Imagen = pygame.image.load("Recursos\Imagenes\imagen.jpg").convert()
# Resolución base y escalado
INTERNAL_WIDTH, INTERNAL_HEIGHT = 704, 384
SCALE = 2
WINDOW_WIDTH, WINDOW_HEIGHT = INTERNAL_WIDTH * SCALE, INTERNAL_HEIGHT * SCALE

# Superficie donde se dibuja la escena base
internal_surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))

#Ventana principal
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Menú Mejorado Pixel Perfect")
clock = pygame.time.Clock()

#fuentes de texto
font = pygame.font.SysFont("Consolas", 15, bold=True)

#  imagen de fondo
background_img = pygame.image.load("Recursos\Imagenes\imagen.jpg").convert()
background_img = pygame.transform.scale(background_img, (INTERNAL_WIDTH, INTERNAL_HEIGHT))

# Clase para botones interactivos
class Button:
    def __init__(self, label, pos, callback, width=200, height=40):
        self.label = label
        self.pos = pos
        self.callback = callback
        self.width = width
        self.height = height
        self.rect = pygame.Rect(pos[0], pos[1], width, height)  # Área interactiva

    def draw(self, surface, mouse_pos, click, bg, hover_bg):
        hovered = self.rect.collidepoint(mouse_pos[0] // SCALE, mouse_pos[1] // SCALE)
        pygame.draw.rect(surface, hover_bg if hovered else bg, self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
        text = font.render(self.label() if callable(self.label) else self.label, True, (255, 255, 255))
        surface.blit(text, (self.pos[0] + 10, self.pos[1] + 8))
        if hovered and click:
            self.callback()

# Clase para paneles de información (ayuda o créditos)
class Panel:
    def __init__(self, lines, close_callback):
        self.lines = lines
        self.close_callback = close_callback

    def draw(self, surface, mouse_pos, click):
        panel_rect = pygame.Rect(40, 40, INTERNAL_WIDTH - 80, INTERNAL_HEIGHT - 80)
        pygame.draw.rect(surface, (30, 30, 30), panel_rect)
        pygame.draw.rect(surface, (255, 255, 255), panel_rect, 2)
        y = 60
        for line in self.lines:
            text = font.render(line, True, (255, 255, 255))
            surface.blit(text, (60, y))
            y += 30
        if click:
            self.close_callback()

# Clase principal del menú
class Menu:
    def __init__(self):
        self.sound_on = True
        self.start_game = False
        self.active_panel = None
        self.sensitivity = 1.0
        self.speed = 1
        self.controller_connected = self.detect_controller()

        # Botones del menú principal
        self.buttons = [
            Button("INICIO", (60, 60), self.start),
            Button("CONFIGURACION", (60, 120), self.toggle_settings),
            Button("CREDITOS", (60, 180), self.show_credits),
            Button("AYUDA", (60, 240), self.show_help),
            Button("SALIR", (60, 300), self.exit_game),
        ]

        # Botones del panel de configuración
        self.settings_buttons = [
            Button(lambda: f"SONIDO: {'ON' if self.sound_on else 'OFF'}", (300, 80), self.toggle_sound),
            Button(lambda: f"SENSIBILIDAD: {self.sensitivity:.1f}", (300, 130), self.adjust_sensitivity),
            Button(lambda: f"VELOCIDAD: {self.speed}", (300, 180), self.adjust_speed),
            Button(lambda: f"MANDO: {'CONECTADO' if self.controller_connected else 'NO CONECTADO'}",
                   (300, 230), self.refresh_controller_status)
        ]

    def start(self):
        self.start_game = True

    def toggle_settings(self):
        self.active_panel = None if self.active_panel else "settings"

    def toggle_sound(self):
        self.sound_on = not self.sound_on

    def adjust_sensitivity(self):
        self.sensitivity += 0.1
        if self.sensitivity > 2.0:
            self.sensitivity = 0.0

    def adjust_speed(self):
        self.speed += 1
        if self.speed > 3:
            self.speed = 1

    def detect_controller(self):
        pygame.joystick.init()
        return pygame.joystick.get_count() > 0

    def refresh_controller_status(self):
        self.controller_connected = self.detect_controller()

    def show_credits(self):
        credit_lines = [
            "Proyecto de semestre",
            "Simulacion de la Hacienda San Jacinto",
            "Integrantes:",
            "-Jessua Rene Solis Juarez",
            "-Kyrsa Jolieth Hernandez Roque",
            "-Vanessa de los Angeles Mercado Ortega",
            "-Alberth Hernan Izaguirre Espinoza",
            "-Grupo: 3T1-COMS",
            "SALIR"
        ]
        self.active_panel = Panel(credit_lines, self.clear_panel)

    def show_help(self):
        help_lines = [
            "Controles del TECLADO",
            "W - Mover hacia arriba",
            "S - Mover hacia abajo",
            "A - Mover a la izquierda",
            "D - Mover a la derecha",
            "Controles del mando",
            "Joystick izquierdo - movimiento",
            "Joystick derecho - rotación de cámara",
            "SALIR"
        ]
        self.active_panel = Panel(help_lines, self.clear_panel)

    def clear_panel(self):
        self.active_panel = None

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def draw(self, mouse_pos, click):
        internal_surface.blit(background_img, (0, 0))
        if isinstance(self.active_panel, Panel):
            self.active_panel.draw(internal_surface, mouse_pos, click)
        elif self.active_panel == "settings":
            for btn in self.settings_buttons:
                btn.draw(internal_surface, mouse_pos, click, (60, 100, 60), (100, 160, 100))
            for btn in self.buttons:
                btn.draw(internal_surface, mouse_pos, False, (90, 72, 145), (130, 110, 200))
        else:
            for btn in self.buttons:
                btn.draw(internal_surface, mouse_pos, click, (90, 72, 145), (130, 110, 200))

def mostrar_menu():
    menu = Menu()
    running = True
    while running:
        if menu.start_game:
            print(">> Aquí iniciaría el juego 3D real")
            break
        mouse_pos = pygame.mouse.get_pos()
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True
        menu.draw(mouse_pos, click)
        scaled_surface = pygame.transform.scale(internal_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    mostrar_menu()
