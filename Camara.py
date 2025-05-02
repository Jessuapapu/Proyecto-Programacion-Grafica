
from OpenGL.GL import *
from OpenGL.GLU import *
import math
class Camaras:

        
    def __init__(self, cam_pos, cam_yaw, velocidad, sensibilidad):
        """ 
            Cam_pos es la posicion de la camara
            Cam_yaw es el eje de vista o de rotacion con respecto a la vista
            Velocidad es la velocidad con la que se mueve la camara
            Sensibilidad es el coefinciente para mover la camara
            
        """
        self.cam_pos = cam_pos
        self.cam_yaw = cam_yaw
        self.velocidad = velocidad
        self.sencibilidad = sensibilidad
        self.cam_target = [] 
        
    def InicializarTarget(self):
        self.cam_target = [
            self.cam_pos[0] + math.sin(math.radians(self.cam_yaw)),
            self.cam_pos[1],
            self.cam_pos[2] - math.cos(math.radians(self.cam_yaw))
        ]


        

        