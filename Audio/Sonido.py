from Audio import Audios

# Instancia compartida de sonido para las escenas.
# Aquí solo se registran los archivos; la reproducción la controla main.py
# (antes este módulo reproducía y detenía sonidos al importarse).
sonido = Audios.Musica()

# Música de fondo
sonido.cargar_musica("musica1", "indian-pacific-271.mp3")

# Uso desde las escenas:
#   sonido.reproducir_musica("musica1", True)
#   sonido.pausar_musica()          # p. ej. para un botón de pausa
#   sonido.cargar_efecto("Efecto_paso", "footstep.mp3")
#   sonido.reproducir_efecto("Efecto_paso")
#   sonido.cerrar_sonidos()         # detiene todos los sonidos
