class Escenas:
    def __init__(self,ListModels:list):
        self.Modelos = ListModels
        
    def DibujarEscena(self):
        for Modelo in self.Modelos:
            Modelo.draw()
        

        
    
        