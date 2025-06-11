import pygame

pygame.init()
font = pygame.font.SysFont("Consolas", 15, bold=True)

# Resolución base y escalado
INTERNAL_WIDTH, INTERNAL_HEIGHT = 704, 384
SCALE = 2
WINDOW_WIDTH, WINDOW_HEIGHT = INTERNAL_WIDTH * SCALE, INTERNAL_HEIGHT * SCALE

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
