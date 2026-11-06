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
        for Modelo in self.Modelos:
            Modelo.draw()
        # Segunda pasada: objetos translúcidos (vidrios), siempre al final
        for Modelo in self.Modelos:
            if hasattr(Modelo, "draw_transparente"):
                Modelo.draw_transparente()
        

        
    
        