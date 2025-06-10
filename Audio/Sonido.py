from Audio import Audios
#Sonidos transfondo
sonido = Audios.Musica()
sonido.cargar_musica("Paseo", "indian-pacific-271.mp3")
sonido.detener_musica()
sonido.reproducir_musica("Paseo", "indian-pacific-271.mp3")
sonido.pausar_musica() #Para usarse en el menu en el boton de pausa
#Efecto de sonido.
sonido.cargar_efecto("Efecto_paso", "footstep.mp3")
sonido.reproducir_efecto("Efecto_paso", "footstep.mp3") #Efecto para implementarse en las escenas desde el main
sonido.cerrar_sonidos() #Esto desactiva todos los sonidos que se pueden presentar
