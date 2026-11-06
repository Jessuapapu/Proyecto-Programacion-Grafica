from OpenGL.GL import *
from OpenGL.GLU import *
import math

class Camaras:
    # camara en primera persona

    def __init__(self, cam_pos: list, cam_yaw: float, cam_pitch: float, velocidad: float, sensibilidad: float, up: list):
        self.cam_pos = cam_pos
        self.cam_yaw = cam_yaw      # horizontal
        self.cam_pitch = cam_pitch  # vertical
        self.velocidad = velocidad  # por cuadro
        self.sensibilidad = sensibilidad
        self.up = up
        self.cam_target = []        # hacia donde mira
        self.ActualizarTarget()

    def ActualizarTarget(self):
        # direccion a partir de yaw y pitch
        rad_yaw = math.radians(self.cam_yaw)
        rad_pitch = math.radians(self.cam_pitch)

        # con yaw = 0 mira hacia -z
        self.cam_target = [
            math.cos(rad_pitch) * math.sin(rad_yaw),
            math.sin(rad_pitch),
            -math.cos(rad_pitch) * math.cos(rad_yaw)
        ]
