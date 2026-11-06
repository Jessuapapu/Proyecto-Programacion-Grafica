# objetos de la escena de la hacienda
import os
import sys
from Clases import Modelo
from Escenas.Arboles import Bosque as _Bosque
from Escenas.Terreno import Terreno as _Terreno
from Escenas.Museo import Museo as _Museo
from Escenas import Iluminacion

# ruta base
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def modelo_path(*relative_path):
    return os.path.join(BASE_PATH, *relative_path)

# el terreno viejo (Tereno) no se dibuja porque ahora hay terreno con relieve
Hacienda = Modelo.Modelos(
    modelo_path("modelosObj", "Hacienda", "Hacienda.obj"),
    modelo_path("modelosObj", "Hacienda", "Hacienda.mtl"),
    None,               # las colisiones las maneja Clases/Colision.py
    excluir_materiales=("Tereno",),
    modos={"Paredes": Iluminacion.MODO_PARED, "Suelo": Iluminacion.MODO_PISO},
)

Mesa = Modelo.Modelos(
    modelo_path("modelosObj", "Mesas", "Mesas.obj"),
    modelo_path("modelosObj", "Mesas", "Mesas.mtl")
)

Armas = Modelo.Modelos(
    modelo_path("modelosObj", "Pistolas", "Guns2.obj"),
    modelo_path("modelosObj", "Pistolas", "Guns2.mtl")
)

Caballo = Modelo.Modelos(
    modelo_path("modelosObj", "Caballos", "Horse.obj"),
    modelo_path("modelosObj", "Caballos", "Horse.mtl")
)

Retrato = Modelo.Modelos(
    modelo_path("modelosObj", "Retratos", "Marcofotos.obj"),
    modelo_path("modelosObj", "Retratos", "Marcofotos.mtl")
)

# de este obj solo dejamos el rifle, los arboles se cambiaron por los low poly
Arbolito = Modelo.Modelos(
    modelo_path("modelosObj", "Arbolitos", "arbolito3.obj"),
    modelo_path("modelosObj", "Arbolitos", "arbolito3.mtl"),
    excluir_materiales=("Material.011", "Material.012"),
)

# terreno y bosque (se generan con generar_mapa.py)
Terreno = _Terreno(modelo_path("modelosObj", "Terreno"))
Bosque = _Bosque(modelo_path("modelosObj", "Terreno", "vegetacion.json"))

# sala de los heroes, los textos estan en museo.json
Museo = _Museo(modelo_path("modelosObj", "Museo"))

# la hacienda tiene que ir primero, main.py usa ListHacienda[0] para las colisiones
ListHacienda = [Hacienda, Terreno, Mesa, Armas, Caballo, Retrato, Arbolito, Museo, Bosque]
