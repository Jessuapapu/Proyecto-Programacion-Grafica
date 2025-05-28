
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

# Estado de sonido
sound_on = True
show_settings = False

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

def draw_background():
    internal_surface.blit(background_img, (0, 0))

def draw_buttons(mouse_pos, click):
    global show_settings, sound_on
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
            if label == "CONFIGURACION":
                show_settings = not show_settings
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

def main():
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        draw_background()
        draw_buttons(mouse_pos, click)

        # Escalado pixel-perfect
        scaled_surface = pygame.transform.scale(internal_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

main()
