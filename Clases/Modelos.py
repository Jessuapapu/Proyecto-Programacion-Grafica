import pywavefront
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

class Modelo:
    def __init__(self,path):
        # Se carga y se guarda el archivo .obj
        self.modelo = pywavefront.Wavefront(path, create_materials=True, collect_faces=True,parse=True)
        
    def DibujarModelo(self):
        # Se dibuja el modelo
        for name, mesh in self.modelo.meshes.items():
            glBegin(GL_TRIANGLES)
            for face in mesh.faces:
                for vertex_i in face:
                    glVertex3f(*self.modelo.vertices[vertex_i])
            glEnd()  
    
    