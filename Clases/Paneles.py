import pygame

pygame.init()
font = pygame.font.SysFont("Consolas", 15, bold=True)
# Resolución base y escalado
INTERNAL_WIDTH, INTERNAL_HEIGHT = 704, 384
SCALE = 2
WINDOW_WIDTH, WINDOW_HEIGHT = INTERNAL_WIDTH * SCALE, INTERNAL_HEIGHT * SCALE

class Panel:
    def __init__(self, lines, close_callback):
        self.lines = lines
        self.close_callback = close_callback

    def draw(self, surface, mouse_pos, click):
        rect = pygame.Rect((INTERNAL_WIDTH - 500) // 2, (INTERNAL_HEIGHT - 300) // 2, 500, 300)
        pygame.draw.rect(surface, (103, 77, 64), rect)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)

        y = rect.top + 20
        for line in self.lines:
            text = font.render(line, True, (255, 255, 255))
            surface.blit(text, (rect.left + 20, y))
            y += 30

        if click:
            self.close_callback()