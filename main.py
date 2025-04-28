# Importamos las librerías necesarias
import pygame                       # Manejar ventana, teclado y mouse
from pygame.locals import *         # Constantes de Pygame (como QUIT, KEYDOWN, etc.)
from OpenGL.GL import *              # Funciones de OpenGL normales (dibujar, etc.)
from OpenGL.GLU import *             # Funciones de cámara (gluPerspective)
import pywavefront                  # Para cargar modelos 3D .obj fácilmente

# Función para cargar un modelo .obj
def load_model(path):
    # pywavefront carga el archivo obj y guarda toda la info del modelo (vértices, caras, etc.)
    return pywavefront.Wavefront(path, create_materials=True, collect_faces=True)

# Función para dibujar el modelo
def draw_model(scene):
    # Recorremos todas las partes (meshes) del modelo
    for name, mesh in scene.meshes.items():
        glBegin(GL_TRIANGLES)  # Vamos a dibujar usando triángulos
        for face in mesh.faces:
            for vertex_i in face:
                # Cada face contiene índices que apuntan a los vértices reales
                # scene.vertices guarda las coordenadas x, y, z
                glVertex3f(*scene.vertices[vertex_i])
        glEnd()
    


# Función principal donde ocurre todo
def main():
    pygame.init()  # Inicializa Pygame

    # Define el tamaño de la ventana
    display = (800, 600)
    # Crea la ventana de doble buffer (mejor rendimiento) y con soporte OpenGL
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Render Modelo Blender")  # Título de la ventana
    
    eye = (0.0, 0.0, 3.0)  # Posición inicial de la cámara
    center = (0.0, 0.0, 0.0)  # Punto al que mira la cámara
    up = (0.0, 1.0, 0.0)  # Vector "up" de la cámara (normalmente (0, 1, 0))

    # Configura la perspectiva de la cámara
    # 45° de apertura, proporción de aspecto (ancho/alto), distancia de visión mínima y máxima
    gluPerspective(45, (display[0] / display[1]), 0.1, 1000.0)

    # Mueve la cámara 5 unidades hacia atrás y 1 unidad hacia abajo
    glTranslatef(0.0, -1.0, -500)

    # Habilita el test de profundidad para que los objetos se dibujen correctamente en 3D
    glEnable(GL_DEPTH_TEST)

    # Cargamos el modelo 3D
    modelo = load_model('modelosObj/Hacienda.obj')

    # Creamos un reloj para controlar la cantidad de frames por segundo
    clock = pygame.time.Clock()

    running = True  # Variable para saber si seguimos ejecutando el programa
    while running:
        clock.tick(60)  # Limitamos el bucle a 60 FPS

        # Capturamos todos los eventos (teclado, cerrar ventana, etc.)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                 
        
         # Detectar teclas
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            rotate_y -= 1
        if keys[pygame.K_RIGHT]:
            rotate_y += 1
        if keys[pygame.K_UP]:
            rotate_x -= 1
        if keys[pygame.K_DOWN]:
            rotate_x += 1
        
        

        # Limpiamos la pantalla
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Dibujamos el modelo
        draw_model(modelo)

        # Actualizamos la ventana
        pygame.display.flip()

    # Cuando salimos del bucle, cerramos Pygame
    pygame.quit()

# Si este archivo se ejecuta directamente, corremos main()
if __name__ == "__main__":
    main()
