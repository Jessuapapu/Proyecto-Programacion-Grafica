import os
import sys
from Clases import Modelo
from Escenas.Arboles import Arboles

# Ruta base dinámica
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Construcción de rutas para modelos
def modelo_path(*relative_path):
    return os.path.join(BASE_PATH, *relative_path)

# Solo la hacienda carga la malla de colisión (es la única que se consulta en main.py);
# antes cada modelo volvía a leer el mismo archivo de 6 MB y el arranque era muy lento.
Hacienda = Modelo.Modelos(
    modelo_path("modelosObj", "Hacienda", "Hacienda.obj"),
    modelo_path("modelosObj", "Hacienda", "Hacienda.mtl"),
    modelo_path("modelosObj", "colision_combined.obj")
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

Arbolito = Modelo.Modelos(
    modelo_path("modelosObj", "Arbolitos", "arbolito3.obj"),
    modelo_path("modelosObj", "Arbolitos", "arbolito3.mtl")
)

# Árboles adicionales: el mismo modelo repetido sobre el terreno.
# (x, y, z, rotación en grados, escala). La altura y sale del terreno de Hacienda.obj y
# las posiciones evitan la casa, los corrales, la cerca de troncos, los caballos y el
# punto de inicio de la cámara.
POSICIONES_ARBOLES = [
    (-66.2, -3.47, 132.5, 326, 0.85), (212.9, -3.47, 191.5, 229, 1.16),
    (6.9, -3.47, 148.6, 161, 0.94), (-101.3, -3.47, -124.8, 189, 0.99),
    (74.4, -3.47, -222.1, 161, 0.95), (-132.5, -2.44, 170.8, 287, 1.08),
    (-70.6, -3.42, 203.7, 203, 0.99), (182.6, -2.88, -82.4, 251, 0.92),
    (105.4, -3.47, 22.1, 224, 0.95), (-36.4, -3.47, -2.4, 169, 1.12),
    (-227.2, -3.41, 134.1, 187, 0.93), (-0.0, -3.47, -185.4, 326, 1.29),
    (125.0, -1.03, 209.1, 320, 1.09), (-154.9, -3.39, 203.9, 9, 0.91),
    (-222.1, -3.47, 47.6, 177, 1.08), (29.2, -3.47, 178.0, 331, 0.85),
    (201.6, -2.40, 131.2, 230, 1.11), (143.3, -1.79, -166.5, 222, 0.97),
    (121.3, -3.43, -197.1, 218, 1.22), (76.9, -3.47, -169.5, 101, 0.77),
    (72.8, -3.47, 173.8, 128, 0.93), (-85.0, -3.47, -174.3, 239, 1.20),
    (209.1, -3.47, 90.7, 268, 1.24), (99.1, -1.99, 156.1, 124, 1.13),
    (47.6, -3.47, -41.3, 37, 0.94), (211.3, -3.32, -129.3, 41, 0.95),
    (132.2, -3.47, -35.1, 66, 1.17), (-118.3, -2.64, 128.3, 132, 0.77),
    (212.2, -3.47, -214.1, 43, 1.01), (30.8, -3.47, 208.8, 337, 0.79),
    (161.1, -1.29, -151.5, 292, 0.91), (159.9, 0.75, 218.7, 99, 1.10),
    (64.7, -3.47, -0.6, 326, 0.85), (125.1, -3.47, 69.4, 74, 1.16),
    (123.8, -3.00, 123.2, 28, 0.87), (180.3, -3.47, 173.0, 74, 1.05),
    (-218.4, -3.47, -99.5, 97, 1.26), (40.1, -3.47, -147.1, 154, 1.02),
    (-221.0, -3.47, -135.4, 311, 1.06), (-61.2, -3.47, -29.5, 280, 1.27),
    (225.1, -3.47, -6.9, 50, 0.76), (-174.3, -3.47, -120.9, 357, 0.84),
    (-177.8, -2.44, 189.7, 224, 1.16), (217.1, -3.47, 26.7, 355, 1.03),
    (-27.5, -3.47, 130.2, 232, 0.86), (6.8, -3.47, -220.5, 315, 1.05),
    (-206.9, -0.62, 199.6, 360, 1.16), (-223.3, -3.47, -178.5, 119, 0.98),
]

Bosque = Arboles(
    Modelo.Modelos(
        modelo_path("modelosObj", "Arbolitos", "arbol.obj"),
        modelo_path("modelosObj", "Arbolitos", "arbol.mtl")
    ),
    POSICIONES_ARBOLES
)

ListHacienda = [Hacienda, Mesa, Armas, Caballo, Retrato, Arbolito, Bosque]
