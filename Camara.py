from OpenGL.GL import *
from OpenGL.GLU import *
import math

class Camaras:
    def __init__(self, cam_pos: list, cam_yaw: float, cam_pitch: float, velocidad: float, sensibilidad: float, up: list):
        self.cam_pos = cam_pos
        self.cam_yaw = cam_yaw      # horizontal
        self.cam_pitch = cam_pitch  # vertical
        self.velocidad = velocidad
        self.sensibilidad = sensibilidad
        self.up = up
        self.cam_target = []
        self.ActualizarTarget()

    def ActualizarTarget(self):
        # Calcula la dirección mirando con yaw y pitch
        rad_yaw = math.radians(self.cam_yaw)
        rad_pitch = math.radians(self.cam_pitch)

        self.cam_target = [
            math.cos(rad_pitch) * math.sin(rad_yaw),
            math.sin(rad_pitch),
            -math.cos(rad_pitch) * math.cos(rad_yaw)
        ]
