from OpenGL.GL import *
from PIL import Image

class Skybox:
    def __init__(self, size=50.0):
        self.size = size
        self.textures_dia = {}
        self.textures_noche = {}

        self.faces_dia = {
            "right": "Recursos/Imagenes/Skybox/Right_5.png",
            "left": "Recursos/Imagenes/Skybox/Left_2.png",
            "top": "Recursos/Imagenes/Skybox/Up_0.png",
            "bottom": "Recursos/Imagenes/Skybox/Down_1.png",
            "front": "Recursos/Imagenes/Skybox/Front_4.png",
            "back": "Recursos/Imagenes/Skybox/Back_3.png"
        }

        self.faces_noche = {
            "right": "Recursos/Imagenes/Skybox/PolygonSciFiSpace_Skybox_01_Right_23.png",
            "left": "Recursos/Imagenes/Skybox/PolygonSciFiSpace_Skybox_01_Left_20.png",
            "top": "Recursos/Imagenes/Skybox/PolygonSciFiSpace_Skybox_01_Up_18.png",
            "bottom": "Recursos/Imagenes/Skybox/PolygonSciFiSpace_Skybox_01_Down_19.png",
            "front": "Recursos/Imagenes/Skybox/PolygonSciFiSpace_Skybox_01_Front_22.png",
            "back": "Recursos/Imagenes/Skybox/PolygonSciFiSpace_Skybox_01_Back_21.png"
        }

        self.load_textures(self.faces_dia, self.textures_dia)
        self.load_textures(self.faces_noche, self.textures_noche)

    def load_textures(self, faces_dict, textures_dict):
        for name, path in faces_dict.items():
            try:
                image = Image.open(path).convert("RGBA").resize((512, 512))
                image = image.rotate(360).transpose(Image.FLIP_LEFT_RIGHT)
                img_data = image.tobytes()

                texture_id = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, texture_id)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

                textures_dict[name] = texture_id
            except Exception as e:
                print(f"Error cargando {path}: {e}")

    def collides(self, pos, buffer=0.1):
        """
        Devuelve True si la posición 'pos' ([x, y, z]) está fuera del cubo del skybox.
        El parámetro 'buffer' añade una holgura antes de la frontera.
        """
        x, y, z = pos
        limit = self.size - buffer
        return abs(x) > limit or abs(y) > limit or abs(z) > limit

    def draw(self, modo_dia=True):
        size = self.size
        glPushMatrix()
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)
        glColor3f(1, 1, 1)

        texturas = self.textures_dia if modo_dia else self.textures_noche

        def draw_face(tex, vertices):
            if tex not in texturas:
                return
            glBindTexture(GL_TEXTURE_2D, texturas[tex])
            glBegin(GL_QUADS)
            for coord, vert in zip([(0,0),(1,0),(1,1),(0,1)], vertices):
                glTexCoord2f(*coord)
                glVertex3f(*vert)
            glEnd()

        draw_face("front",  [(-size,-size,-size),( size,-size,-size),( size, size,-size),(-size, size,-size)])
        draw_face("back",   [( size,-size, size),(-size,-size, size),(-size, size, size),( size, size, size)])
        draw_face("left",   [(-size,-size, size),(-size,-size,-size),(-size, size,-size),(-size, size, size)])
        draw_face("right",  [( size,-size,-size),( size,-size, size),( size, size, size),( size, size,-size)])
        draw_face("top",    [(-size, size,-size),( size, size,-size),( size, size, size),(-size, size, size)])
        draw_face("bottom", [(-size,-size, size),( size,-size, size),( size,-size,-size),(-size,-size,-size)])

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()
