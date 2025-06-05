import pygame
import sys
from PIL import Image
pygame.init()

# Imagen = pygame.image.load("Recursos\Imagenes\imagen.jpg").convert()
# Resolución base y escalado
INTERNAL_WIDTH, INTERNAL_HEIGHT = 704, 384
SCALE = 2
WINDOW_WIDTH, WINDOW_HEIGHT = INTERNAL_WIDTH * SCALE, INTERNAL_HEIGHT * SCALE

# Crear superficie base y pantalla
internal_surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Menú Mejorado Pixel Perfect")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 15, bold=True)

# Cargar imagen de fondo
background_img = pygame.image.load("Recursos\Imagenes\imagen.jpg").convert()
background_img = pygame.transform.scale(background_img, (INTERNAL_WIDTH, INTERNAL_HEIGHT))

# === CLASES ===
class Button:
    def __init__(self, label, pos, callback, width=200, height=40):
        self.label = label
        self.pos = pos
        self.callback = callback
        self.width = width
        self.height = height

    def draw(self, surface, mouse_pos, click, bg, hover_bg):
        x, y = self.pos
        rect = pygame.Rect(x, y, self.width, self.height)
        hovered = rect.collidepoint(mouse_pos[0] // SCALE, mouse_pos[1] // SCALE)

        pygame.draw.rect(surface, hover_bg if hovered else bg, rect)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)

        text = font.render(
            self.label() if callable(self.label) else self.label, True, (255, 255, 255)
        )
        surface.blit(text, (x + 10, y + 8))

        if hovered and click:
            self.callback()


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


class Menu:
    def __init__(self):
        self.sound_on = True
        self.start_game = False
        self.active_panel = None

        self.buttons = [
            Button("INICIO", (60, 60), self.start),
            Button("CONFIGURACION", (60, 120), self.toggle_settings),
            Button("CREDITOS", (60, 180), self.show_credits),
            Button("AYUDA", (60, 240), self.show_help),
            Button("SALIR", (60, 300), self.exit_game),
        ]

        self.settings_buttons = [
            Button(lambda: f"SONIDO: {'ON' if self.sound_on else 'OFF'}", (300, 120), self.toggle_sound)
        ]

    def start(self):
        self.start_game = True

    def toggle_settings(self):
        self.active_panel = None if self.active_panel else "settings"

    def toggle_sound(self):
        self.sound_on = not self.sound_on

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
            "W - Mover a hacia Arriba",
            "S - Mover a hacia Abajo",
            "A - Mover hacia a la Izquierda",
            "D - Mover hacia a laDerecha",
            "Controles del mando",
            "Joystick izquierdo - movimiento",
            "Joystick Derecho  - Rotacion de Camara",
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
                btn.draw(internal_surface, mouse_pos, False, (90, 72, 145), (130, 110, 200))  # no click

        else:
            for btn in self.buttons:
                btn.draw(internal_surface, mouse_pos, click, (90, 72, 145), (130, 110, 200))


# === EJECUCIÓN ===
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


# Iniciar
mostrar_menu()