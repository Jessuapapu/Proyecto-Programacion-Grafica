from OpenGL.GL import *
from PIL import Image

class Skybox:
    def __init__(self, size=50.0):
        self.size = size
        self.textures = {}
        self.faces = {
            "right": "Recursos/Imagenes/Skybox/Right_5.png",
            "left": "Recursos/Imagenes/Skybox/Left_2.png",
            "top": "Recursos/Imagenes/Skybox/Up_0.png",
            "bottom": "Recursos/Imagenes/Skybox/Down_1.png",
            "front": "Recursos/Imagenes/Skybox/Front_4.png",
            "back": "Recursos/Imagenes/Skybox/Back_3.png"
        }
        self.load_textures()

    def load_textures(self):
        for name, path in self.faces.items():
            image = Image.open(path).convert("RGBA").resize((512, 512))
            # Corrige las imagenes que estan al reves XD
            image = image.rotate(360).transpose(Image.FLIP_LEFT_RIGHT)
            img_data = image.tobytes()

            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            self.textures[name] = texture_id

    def draw(self):
        size = self.size
        glPushMatrix()
        glEnable(GL_TEXTURE_2D)
        # Esto evita que oculte los objetos
        glDisable(GL_DEPTH_TEST)
        glColor3f(1, 1, 1)

        def draw_face(tex, v):
            glBindTexture(GL_TEXTURE_2D, self.textures[tex])
            glBegin(GL_QUADS)
            for coord, vert in zip([(0,0),(1,0),(1,1),(0,1)], v):
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
