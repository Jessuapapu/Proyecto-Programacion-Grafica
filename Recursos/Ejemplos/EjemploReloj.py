
import pygame


# Inicializar Pygame
pygame.init()


class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 25)

    def tprint(self, screen, text):
        text_bitmap = self.font.render(text, True, (0, 0, 0))
        screen.blit(text_bitmap, (self.x, self.y))
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10




printf = TextPrint()


# Configurar la ventana
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Mi Juego con Reloj")

# Crear el objeto Clock
clock = pygame.time.Clock()
segundossss = 0
segundosss = 0


# Bucle principal del juego
running = True
while running:
    # Manejar eventos (p.ej., cerrar la ventana)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
    # Controlar la velocidad de los fotogramas
    clock.tick(60)    
            
    screen.fill((255, 255, 255))
    printf.reset()       
            
    # esta es una forma pero es desde se inicializo el pygame.init()
    segundoss = pygame.time.get_ticks()/1000
    printf.tprint(screen,str(segundoss))
        
    # se obtine el frame actual divideindoo y sumando se puede, pero este pierde sincronia entre los segundos 7 y 8, con respecto a los otros
    segundosss += clock.get_rawtime()/60
    printf.tprint(screen,str(segundosss))
            
    # ya que el reloj esta en 60 pygame trata de generar 0 frames cada 1 segundo, es decir, por cada 60 repeticiones del ciclo while es un segundo        
    printf.tprint(screen,str(segundossss))
    
    # Actualizar la pantalla
    pygame.display.flip()
    segundossss += 1/60

       

# Salir de Pygame
pygame.quit()