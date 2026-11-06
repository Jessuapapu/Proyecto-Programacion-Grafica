# lista de objetos de la escena, cada uno con cargarmodelos, draw y liberar


class Escenas:
    def __init__(self,ListModels:list):
        self.Modelos = ListModels
    
    def cargar(self):
        for Modelo in self.Modelos:
            Modelo.cargarmodelos()
             
    
    def liberar(self):
        for Modelo in self.Modelos:
            Modelo.liberar()

    def DibujarEscena(self):
        # primero lo opaco
        for Modelo in self.Modelos:
            Modelo.draw()
        # despues lo transparente (vidrios)
        for Modelo in self.Modelos:
            if hasattr(Modelo, "draw_transparente"):
                Modelo.draw_transparente()
        

        
    
        