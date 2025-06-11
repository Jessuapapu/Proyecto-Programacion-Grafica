import pygame

# Fuente
pygame.init()
font = pygame.font.SysFont("Consolas", 15, bold=True)

# Resolución base y escalado
INTERNAL_WIDTH, INTERNAL_HEIGHT = 704, 384
SCALE = 2
WINDOW_WIDTH, WINDOW_HEIGHT = INTERNAL_WIDTH * SCALE, INTERNAL_HEIGHT * SCALE

class Slider:
    def __init__(self, name, label, pos, min_val, max_val, step, value):
        self.name = name
        self.label = label
        self.pos = pos
        self.min = min_val
        self.max = max_val
        self.step = step
        self.value = value  # ← variable simple
        self.width = 150
        self.height = 8

    def draw(self, surface, mouse_pos, click):
        x, y = self.pos
        pygame.draw.rect(surface, (100, 100, 100), (x, y, self.width, self.height))

        percent = (self.value - self.min) / (self.max - self.min)
        knob_x = x + int(percent * self.width)
        pygame.draw.circle(surface, (255, 255, 255), (knob_x, y + self.height // 2), 6)

        text = font.render(f"{self.label}: {self.value}", True, (255, 255, 255))
        surface.blit(text, (x, y - 20))

        if click and pygame.Rect(x, y, self.width, self.height).collidepoint(mouse_pos[0] // SCALE, mouse_pos[1] // SCALE):
            rel_x = (mouse_pos[0] // SCALE) - x
            new_value = self.min + (rel_x / self.width) * (self.max - self.min)
            self.value = max(self.min, min(self.max, round(new_value / self.step) * self.step))
