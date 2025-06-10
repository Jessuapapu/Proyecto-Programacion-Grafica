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

    def draw(self, surface, mouse_pos, click, bg, hover_bg):
        x, y = self.pos
        rect = pygame.Rect(x, y, self.width, self.height)
        hovered = rect.collidepoint(mouse_pos[0] // SCALE, mouse_pos[1] // SCALE)
        pygame.draw.rect(surface, hover_bg if hovered else bg, rect, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=10)
        text = font.render(self.label() if callable(self.label) else self.label, True, (255, 255, 255))
        surface.blit(text, (x + 10, y + 8))
        if hovered and click:
            self.callback()

# --- Clase para barras deslizantes (sliders) ---
class Slider:
    def __init__(self, label, pos, min_val, max_val, step, value_ref):
        self.label = label
        self.pos = pos
        self.min = min_val
        self.max = max_val
        self.step = step
        self.value_ref = value_ref
        self.width = 150
        self.height = 8

    def draw(self, surface, mouse_pos, click):
        x, y = self.pos
        pygame.draw.rect(surface, (100, 100, 100), (x, y, self.width, self.height))
        percent = (self.value_ref["value"] - self.min) / (self.max - self.min)
        knob_x = x + int(percent * self.width)
        pygame.draw.circle(surface, (255, 255, 255), (knob_x, y + self.height // 2), 6)
        text = font.render(f"{self.label}: {self.value_ref['value']}", True, (255, 255, 255))
        surface.blit(text, (x, y - 20))

        if click and pygame.Rect(x, y, self.width, self.height).collidepoint(mouse_pos[0] // SCALE, mouse_pos[1] // SCALE):
            rel_x = (mouse_pos[0] // SCALE) - x
            new_value = self.min + (rel_x / self.width) * (self.max - self.min)
            self.value_ref["value"] = max(self.min, min(self.max, round(new_value / self.step) * self.step))

# --- Clase para paneles de texto (Créditos, Ayuda) ---
class Panel:
    def __init__(self, lines, close_callback):
        self.lines = lines
        self.close_callback = close_callback

    def draw(self, surface, mouse_pos, click):
        rect = pygame.Rect(40, 40, INTERNAL_WIDTH - 80, INTERNAL_HEIGHT - 80)
        pygame.draw.rect(surface, (103, 77, 64), rect)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)
        y = 60
        for line in self.lines:
            text = font.render(line, True, (255, 255, 255))
            surface.blit(text, (60, y))
            y += 30
        if click:
            self.close_callback()

# --- Clase personalizada para el panel de configuración con tamaño reducido ---
class SettingsPanel:
    def __init__(self, sliders, close_callback, controller_ref):
        self.sliders = sliders
        self.close_callback = close_callback
        self.controller_ref = controller_ref

    def draw(self, surface, mouse_pos, click):
        rect = pygame.Rect(40, 40, INTERNAL_WIDTH - 80, INTERNAL_HEIGHT - 80)
        pygame.draw.rect(surface, (103, 77, 64), rect)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)

        for item in self.sliders:
            if isinstance(item, Slider):
                item.draw(surface, mouse_pos, click)
            else:
                item.draw(surface, mouse_pos, click, (160, 82, 45), (190, 112, 75))

        status = "CONECTADO" if self.controller_ref["value"] else "NO CONECTADO"
        text = font.render(f"CONTROL: {status}", True, (255, 255, 255))
        surface.blit(text, (300, 220))

        pygame.mixer.music.set_volume(self.sliders[0].value_ref["value"] / 3)

        if click:
            mouse_rect = pygame.Rect(mouse_pos[0] // SCALE, mouse_pos[1] // SCALE, 1, 1)
            if not rect.contains(mouse_rect):
                self.close_callback()

# --- Clase principal del menú ---
class Menu:
    def __init__(self):
        self.sound_on = {"value": 1}
        self.sensibilidad = {"value": 1.0}
        self.velocidad = {"value": 1}
        self.controller_connected = {"value": pygame.joystick.get_count() > 0}

        self.start_game = False
        self.active_panel = None

        self.buttons = [
            Button("INICIO", (60, 60), self.start),
            Button("CONFIGURACION", (60, 120), self.toggle_settings),
            Button("CREDITOS", (60, 180), self.show_credits),
            Button("AYUDA", (60, 240), self.show_help),
            Button("SALIR", (60, 300), self.exit_game)
        ]

        self.settings_buttons = [
            Slider("SONIDO", (300, 70), 0, 3, 1, self.sound_on),
            Slider("SENSIBILIDAD", (300, 130), 0.0, 2.0, 0.1, self.sensibilidad),
            Slider("VELOCIDAD", (300, 180), 1, 3, 1, self.velocidad),
            Button("REGRESAR", (300, 250), self.clear_panel, 150, 30)
        ]

    def start(self):
        self.start_game = True

    def toggle_settings(self):
        self.controller_connected["value"] = pygame.joystick.get_count() > 0
        self.active_panel = SettingsPanel(self.settings_buttons, self.clear_panel, self.controller_connected)

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def show_credits(self):
        self.active_panel = Panel([
            "Proyecto de semestre",
            "Simulación de la Hacienda San Jacinto",
            "Integrantes:",
            "- Jessua Rene Solis Juarez",
            "- Kyrsa Jolieth Hernandez Roque",
            "- Vanessa de los Angeles Mercado Ortega",
            "- Alberth Hernan Izaguirre Espinoza",
            "Grupo: 3T1-COMS",
            "REGRESAR"
        ], self.clear_panel)

    def show_help(self):
        self.active_panel = Panel([
            "Controles del teclado:",
            "W - Mover hacia arriba",
            "S - Mover hacia abajo",
            "A - Mover a la izquierda",
            "D - Mover a la derecha",
            "Joystick izquierdo - Movimiento",
            "Joystick derecho - Cámara",
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

# Función principal para mostrar el menú y manejar el loop de eventos
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

# Ejecutar el menú si se corre este script directamente
if __name__ == "__main__":
    mostrar_menu()