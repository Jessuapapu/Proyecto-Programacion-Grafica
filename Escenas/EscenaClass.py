class Escenas:
    def __init__(self,ListModels:list):
        self.Modelos = ListModels
    
    def cargar(self):
        for Modelo in self.Modelos:
            Modelo.cargarmodelos()
             
    
    def DibujarEscena(self):
        for Modelo in self.Modelos:
            Modelo.draw()
        

        
    
        