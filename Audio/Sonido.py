from Audio import Audios

sonido = Audios.Musica()
sonido.cargar_musica("Paseo", "indian-pacific-271.mp3")
sonido.detener_musica()
sonido.reproducir_musica("Paseo", "indian-pacific-271.mp3")
sonido.pausar_musica() #Para usarse en el menu en el boton de pausa

sonido.cargar_efecto("Efecto", "sound-effects-multiple-gun-shot-247125.mp3")
sonido.reproducir_efecto("Efecto", "sound-effects-multiple-gun-shot-247125.mp3") #Efecto de sonido de disparos para implementarse en las escenas desde el main
sonido.cerrar_sonidos() #Esto desactiva todos los sonidos que se pueden presentar
