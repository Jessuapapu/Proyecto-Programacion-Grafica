from Audio import Audios
#Sonidos transfondo
sonido = Audios.Musica()
sonido.cargar_musica("musica1","indian-pacific-271.mp3")
sonido.detener_musica()
sonido.reproducir_musica("musica1",True)
sonido.pausar_musica() #Para usarse en el menu en el boton de pausa
#Efecto de sonido.
sonido.cargar_efecto("Efecto_paso", "footstep.mp3")
sonido.reproducir_efecto("Efecto_paso") #Efecto para implementarse en las escenas desde el main
sonido.cerrar_sonidos() #Esto desactiva todos los sonidos que se pueden presentar
