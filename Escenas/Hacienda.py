import os
import sys
from Clases import Modelo
from Escenas.Arboles import Bosque as _Bosque
from Escenas.Terreno import Terreno as _Terreno
from Escenas import Iluminacion

# Ruta base dinámica
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Construcción de rutas para modelos
def modelo_path(*relative_path):
    return os.path.join(BASE_PATH, *relative_path)

# Solo la hacienda carga la malla de colisión (es la única que se consulta en main.py).
# El terreno viejo ("Tereno") ya no se dibuja: lo reemplaza el terreno con relieve, y
# colision_hacienda.obj es la colisión original sin ese suelo.
Hacienda = Modelo.Modelos(
    modelo_path("modelosObj", "Hacienda", "Hacienda.obj"),
    modelo_path("modelosObj", "Hacienda", "Hacienda.mtl"),
    modelo_path("modelosObj", "colision_hacienda.obj"),
    excluir_materiales=("Tereno",),
    modos={"Paredes": Iluminacion.MODO_PARED},
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

# De arbolito3.obj solo queda el rifle que estaba dentro del archivo; sus árboles
# viejos se reemplazaron por árboles low-poly nuevos en los mismos lugares.
Arbolito = Modelo.Modelos(
    modelo_path("modelosObj", "Arbolitos", "arbolito3.obj"),
    modelo_path("modelosObj", "Arbolitos", "arbolito3.mtl"),
    excluir_materiales=("Material.011", "Material.012"),
)

# Terreno con relieve y bosque low-poly (generados con Recursos/Herramientas/generar_mapa.py)
Terreno = _Terreno(modelo_path("modelosObj", "Terreno"))
Bosque = _Bosque(modelo_path("modelosObj", "Terreno", "vegetacion.json"))

ListHacienda = [Hacienda, Terreno, Mesa, Armas, Caballo, Retrato, Arbolito, Bosque]
