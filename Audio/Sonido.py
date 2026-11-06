from Audio import Audios

# objeto de sonido que se usa en todo el juego
# aqui solo se cargan los archivos, main.py es el que reproduce
sonido = Audios.Musica()

# musica de fondo
sonido.cargar_musica("musica1", "indian-pacific-271.mp3")

# ejemplos:
#   sonido.reproducir_musica("musica1", True)
#   sonido.cargar_efecto("Efecto_paso", "footstep.mp3")
#   sonido.reproducir_efecto("Efecto_paso")
