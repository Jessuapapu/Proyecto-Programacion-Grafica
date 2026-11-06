import pygame

class Joycon:
    # lectura del control. si no hay control las palancas devuelven [0, 0]

    def __init__(self, ZonaMuerta, SensibilidadC, id=0, IDV=1):
        self.id = id
        self.PalancaDerecha = [0, 0]
        self.PalancaIzquierda = [0, 0]
        self.ZonaMuerta = ZonaMuerta    # valores menores a esto cuentan como 0
        self.IDV = IDV                  # 1 o -1 para invertir
        self.JoyStick = None
        self.Sensi = SensibilidadC      # sensibilidad de la camara

        try:
            if pygame.joystick.get_count() > id:
                self.JoyStick = pygame.joystick.Joystick(id)
                self.JoyStick.init()
        except:
            self.JoyStick = None

    def get_PalancaDerecha(self):
        # palanca derecha (camara)

        if self.JoyStick is None:
            return [0, 0]
        
        return [
                self.AplicarZonaMuerta(self.JoyStick.get_axis(2)),
                self.AplicarZonaMuerta(self.JoyStick.get_axis(3))
                ]

    def get_PalancaIzquierda(self):
        # palanca izquierda (movimiento)
        
        if self.JoyStick is None:
            return [0, 0]
            
        return [
                self.AplicarZonaMuerta(self.JoyStick.get_axis(0)),
                self.AplicarZonaMuerta(self.JoyStick.get_axis(1))
            ]


    def AplicarZonaMuerta(self, valor):
        # quita la zona muerta y reescala el resto de 0 a 1
        if abs(valor) < self.ZonaMuerta:
            return 0
        return (abs(valor) - self.ZonaMuerta) / (1 - self.ZonaMuerta) * (1 if valor > 0 else -1)
    

    def desactivar(self):
        self.JoyStick = None
