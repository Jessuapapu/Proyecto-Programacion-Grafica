import pygame

class Joycon:
    def __init__(self, ZonaMuerta, SensibilidadC, id=0, IDV=1):
        self.id = id
        self.PalancaDerecha = [0, 0]
        self.PalancaIzquierda = [0, 0]
        self.ZonaMuerta = ZonaMuerta
        self.IDV = IDV
        self.JoyStick = None
        self.Sensi = SensibilidadC

        try:
            if pygame.joystick.get_count() > id:
                self.JoyStick = pygame.joystick.Joystick(id)
                self.JoyStick.init()
        except:
            self.JoyStick = None

    def get_PalancaDerecha(self):

        if self.JoyStick is None:
            return [0, 0]
        
        return [
                self.AplicarZonaMuerta(self.JoyStick.get_axis(2)),
                self.AplicarZonaMuerta(self.JoyStick.get_axis(3))
                ]

    def get_PalancaIzquierda(self):
        
        if self.JoyStick is None:
            return [0, 0]
            
        return [
                self.AplicarZonaMuerta(self.JoyStick.get_axis(0)),
                self.AplicarZonaMuerta(self.JoyStick.get_axis(1))
            ]


    def AplicarZonaMuerta(self, valor):
        if abs(valor) < self.ZonaMuerta:
            return 0
        return (abs(valor) - self.ZonaMuerta) / (1 - self.ZonaMuerta) * (1 if valor > 0 else -1)
    

    def desactivar(self):
        self.JoyStick = None
