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
                print(f"[Joycon] Conectado: {self.JoyStick.get_name()}")
        except Exception as e:
            print(f"[Joycon] Error inicializando joystick: {e}")
            self.JoyStick = None

    def get_PalancaDerecha(self):
        try:
            if self.JoyStick is None:
                return [0, 0]
            return [
                self.AplicarZonaMuerta(self.JoyStick.get_axis(2)),
                self.AplicarZonaMuerta(self.JoyStick.get_axis(3))
            ]
        except Exception as e:
            print(f"[Joycon] Error PalancaDerecha: {e}")
            self.desactivar()
            return [0, 0]

    def get_PalancaIzquierda(self):
        try:
            if self.JoyStick is None:
                return [0, 0]
            return [
                self.AplicarZonaMuerta(self.JoyStick.get_axis(0)),
                self.AplicarZonaMuerta(self.JoyStick.get_axis(1))
            ]
        except Exception as e:
            print(f"[Joycon] Error PalancaIzquierda: {e}")
            self.desactivar()
            return [0, 0]

    def AplicarZonaMuerta(self, valor):
        if abs(valor) < self.ZonaMuerta:
            return 0
        return (abs(valor) - self.ZonaMuerta) / (1 - self.ZonaMuerta) * (1 if valor > 0 else -1)

    def desactivar(self):
        print("[Joycon] Control desconectado.")
        self.JoyStick = None
