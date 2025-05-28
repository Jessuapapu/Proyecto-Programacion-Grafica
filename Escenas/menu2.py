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
font = pygame.font.SysFont("Courier New", 20, bold=True)

# Cargar imagen de fondo
background_img = pygame.image.load("Recursos\Imagenes\imagen.jpg").convert()
background_img = pygame.transform.scale(background_img, (INTERNAL_WIDTH, INTERNAL_HEIGHT))

# Estado 
sound_on = True
show_settings = False
show_credits= False
show_help= False
start_game=False


# Botones principales y de configuración
buttons = [
    {"label": "INICIO", "pos": (80, 60)},
    {"label": "CONFIGURACION", "pos": (80, 120)},
    {"label": "CREDITOS", "pos": (80, 180)},
    {"label": "AYUDA", "pos": (80, 240)},
    {"label": "SALIR", "pos": (80, 300)}
]

settings_buttons = [
    {"label": lambda: f"SONIDO: {'ON' if sound_on else 'OFF'}", "pos": (300, 120)}
]

credit_lines = [
    "Proyecto de semestre",
    "Simulacion de la Hacienda San Jacinto",
    "Integrantes:",
    "Jessua Rene Solis Juarez",
    "Kyrsa Jolieth Hernandez Roque",
    "Vanessa de los Angeles Mercado Ortega",
    "Alberth Hernan Izaguirre Espinoza",
    "Grupo: 3T1-COMS",
    "REGRESAR"
]

help_lines=[
     "Controles del TECLADO:",
    "W - Mover hacia arriba",
    "S - Mover hacia abajo",
    "A - Mover a la izquierda",
    "D - Mover a la derecha",
    "REGRESAR"
]
def draw_background():
    internal_surface.blit(background_img, (0, 0))

def draw_buttons(mouse_pos, click):
    global show_settings, show_credits, show_help, sound_on, start_game
    for btn in buttons:
        label = btn["label"]
        x, y = btn["pos"]
        rect = pygame.Rect(x, y, 200, 40)
        hovered = rect.collidepoint(mouse_pos[0] // SCALE, mouse_pos[1] // SCALE)
        pygame.draw.rect(internal_surface, (90, 72, 145) if not hovered else (130, 110, 200), rect)
        pygame.draw.rect(internal_surface, (255, 255, 255), rect, 2)
        text = font.render(label, True, (255, 255, 255))
        internal_surface.blit(text, (x + 10, y + 8))
        if hovered and click:
            if label == "INICIO":
                start_game = True
            elif label == "CONFIGURACION":
                show_settings = not show_settings
                show_credits = False
                show_help = False
            elif label == "CREDITOS":
                show_credits = True
                show_settings = False
                show_help = False
            elif label == "AYUDA":
                show_help = True
                show_credits = False
                show_settings = False
            elif label == "SALIR":
                pygame.quit()
                sys.exit()

    if show_settings:
        for btn in settings_buttons:
            label = btn["label"]() if callable(btn["label"]) else btn["label"]
            x, y = btn["pos"]
            rect = pygame.Rect(x, y, 200, 40)
            hovered = rect.collidepoint(mouse_pos[0] // SCALE, mouse_pos[1] // SCALE)
            pygame.draw.rect(internal_surface, (60, 100, 60) if not hovered else (100, 160, 100), rect)
            pygame.draw.rect(internal_surface, (255, 255, 255), rect, 2)
            text = font.render(label, True, (255, 255, 255))
            internal_surface.blit(text, (x + 10, y + 8))
            if hovered and click:
                sound_on = not sound_on

def draw_text_panel(lines, mouse_pos, click):
    global show_credits, show_help
    panel_rect = pygame.Rect(40, 40, INTERNAL_WIDTH - 80, INTERNAL_HEIGHT - 80)
    pygame.draw.rect(internal_surface, (30, 30, 30), panel_rect)
    pygame.draw.rect(internal_surface, (255, 255, 255), panel_rect, 2)

    y = 60
    for line in lines:
        text = font.render(line, True, (255, 255, 255))
        internal_surface.blit(text, (60, y))
        y += 30

    if click:
        show_credits = False
        show_help = False

def montrar_menu():
    global show_credits, show_help, start_game
    running = True
    while running:
        if start_game:
            print(">> Aquí iniciaría el juego 3D real")
            running = False
            break

        mouse_pos = pygame.mouse.get_pos()
        click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        draw_background()

        if show_credits:
            draw_text_panel(credit_lines, mouse_pos, click)
        elif show_help:
            draw_text_panel(help_lines, mouse_pos, click)
        else:
            draw_buttons(mouse_pos, click)

        scaled_surface = pygame.transform.scale(internal_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
