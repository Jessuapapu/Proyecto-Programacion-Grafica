import os
import math
from collections import defaultdict

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.arrays import vbo

from Escenas import Iluminacion as _iluminacion

# Cada vértice del VBO: posición (3) + coordenada de textura (2) + normal (3)
FLOATS_POR_VERTICE = 8
STRIDE = FLOATS_POR_VERTICE * 4

# Constantes de la extensión de filtrado anisotrópico (no siempre expuestas por PyOpenGL)
_GL_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FE
_GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FF

# Caché global de texturas: ruta absoluta -> (id OpenGL, tiene_transparencia)
_cache_texturas = {}
_textura_blanca = None


def textura_blanca():
    """Textura 1x1 blanca para materiales sin imagen (el color sale de Kd)."""
    global _textura_blanca
    if _textura_blanca is None:
        _textura_blanca = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, _textura_blanca)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 1, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, b'\xff\xff\xff\xff')
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)
    return _textura_blanca


def _es_puntero_lfs(ruta):
    """Detecta si el archivo es un puntero de Git LFS en lugar del archivo real."""
    try:
        with open(ruta, 'rb') as f:
            return f.read(64).startswith(b'version https://git-lfs')
    except OSError:
        return False


def _verificar_archivo(ruta):
    if not os.path.isfile(ruta):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")
    if _es_puntero_lfs(ruta):
        raise RuntimeError(
            f"'{ruta}' es un puntero de Git LFS, no el modelo real.\n"
            "Instala Git LFS y descarga los modelos con:\n"
            "    git lfs install\n"
            "    git lfs pull"
        )


def _indice_obj(token, total):
    """Convierte un índice OBJ (1-based, admite negativos) a índice de lista."""
    i = int(token)
    return i - 1 if i > 0 else total + i


def _material_defecto():
    return {
        'kd': [0.8, 0.8, 0.8],
        'ks': [0.5, 0.5, 0.5],
        'ns': 50.0,
        'textura': None,          # nombre de archivo de map_Kd
        'escala_uv': (1.0, 1.0),  # opción -s de map_Kd
        'offset_uv': (0.0, 0.0),  # opción -o de map_Kd
        'tex_id': None,
        'transparente': False,
    }


def _parsear_map(resto):
    """Separa las opciones (-s, -o, -bm, ...) del nombre de archivo de un map_*.
    El nombre de archivo puede contener espacios (p. ej. 'plants atlas.png')."""
    tokens = resto.split()
    opciones = {}
    i = 0
    while i < len(tokens) and tokens[i].startswith('-'):
        nombre = tokens[i][1:]
        i += 1
        valores = []
        if nombre in ('s', 'o', 't'):
            while i < len(tokens) and len(valores) < 3:
                try:
                    valores.append(float(tokens[i]))
                    i += 1
                except ValueError:
                    break
        elif nombre == 'mm':
            valores = tokens[i:i + 2]
            i += 2
        else:
            valores = tokens[i:i + 1]
            i += 1
        opciones[nombre] = valores
    archivo = ' '.join(tokens[i:]).replace('\\', '/')
    # Las rutas absolutas exportadas desde Blender (C:/Users/...) se reducen al nombre del archivo
    return os.path.basename(archivo), opciones


class Modelos:
    def __init__(self, path_obj, path_mtl, path_colision=None, culling_dist=300.0, cell_size=4.0, collision_radius=0.6,
                 excluir_materiales=(), modos=None):
        """excluir_materiales: materiales del OBJ que no se cargan (p. ej. el terreno viejo).
        modos: material -> modo de sombreado especial del shader (ver Iluminacion.MODO_*)."""
        self.excluir_materiales = set(excluir_materiales)
        self.modos = dict(modos or {})
        self.materiales = {}          # material -> propiedades
        self.vbos = {}                # material -> (VBO, cantidad de vértices)
        self.bounding_boxes = {}      # material -> (min, max)
        self._datos = {}              # material -> np.array (N, 8) antes de subirlo a la GPU

        self.path_obj = path_obj
        self.path_mtl = path_mtl
        self.path_colision = path_colision

        # Parámetros de colisión y culling
        self.collision_cells = defaultdict(list)
        self.cell_size = cell_size
        self.collision_radius = collision_radius
        self.culling_distance = culling_dist

    # ------------------------------------------------------------------ MTL
    def _load_mtl(self, ruta_mtl):
        actual = None
        with open(ruta_mtl, 'r', encoding='utf-8', errors='ignore') as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith('#'):
                    continue
                partes = linea.split(None, 1)
                clave = partes[0]
                resto = partes[1].strip() if len(partes) > 1 else ''

                if clave == 'newmtl':
                    actual = resto
                    self.materiales[actual] = _material_defecto()
                    continue
                if actual is None:
                    continue
                m = self.materiales[actual]
                try:
                    if clave == 'Kd':
                        m['kd'] = [float(x) for x in resto.split()[:3]]
                    elif clave == 'Ks':
                        m['ks'] = [float(x) for x in resto.split()[:3]]
                    elif clave == 'Ns':
                        m['ns'] = float(resto.split()[0])
                    elif clave == 'map_Kd':
                        archivo, opciones = _parsear_map(resto)
                        m['textura'] = archivo
                        if 's' in opciones and len(opciones['s']) >= 2:
                            m['escala_uv'] = (opciones['s'][0], opciones['s'][1])
                        if 'o' in opciones and len(opciones['o']) >= 2:
                            m['offset_uv'] = (opciones['o'][0], opciones['o'][1])
                except (ValueError, IndexError):
                    print(f"⚠️ Línea MTL inválida en {ruta_mtl}: {linea}")

    # ------------------------------------------------------------------ OBJ
    def _load_obj(self, ruta_obj):
        posiciones, uvs, normales = [], [], []
        datos = defaultdict(list)
        actual = '__defecto__'

        with open(ruta_obj, 'r', encoding='utf-8', errors='ignore') as f:
            for linea in f:
                if linea.startswith('v '):
                    posiciones.append(tuple(float(x) for x in linea.split()[1:4]))
                elif linea.startswith('vt '):
                    p = linea.split()
                    uvs.append((float(p[1]), float(p[2]) if len(p) > 2 else 0.0))
                elif linea.startswith('vn '):
                    normales.append(tuple(float(x) for x in linea.split()[1:4]))
                elif linea.startswith('usemtl'):
                    partes = linea.split(None, 1)
                    actual = partes[1].strip() if len(partes) > 1 else '__defecto__'
                elif linea.startswith('f '):
                    vertices = []
                    for token in linea.split()[1:]:
                        idx = token.split('/')
                        vi = _indice_obj(idx[0], len(posiciones))
                        ti = _indice_obj(idx[1], len(uvs)) if len(idx) > 1 and idx[1] else None
                        ni = _indice_obj(idx[2], len(normales)) if len(idx) > 2 and idx[2] else None
                        vertices.append((vi, ti, ni))
                    if len(vertices) < 3:
                        continue

                    destino = datos[actual]
                    # Triangulación en abanico: soporta quads y polígonos de N lados
                    for k in range(1, len(vertices) - 1):
                        tri = (vertices[0], vertices[k], vertices[k + 1])
                        pts = [posiciones[v[0]] for v in tri]
                        normal_cara = None
                        if any(v[2] is None for v in tri):
                            normal_cara = self._normal_cara(*pts)
                        for (vi, ti, ni), p in zip(tri, pts):
                            uv = uvs[ti] if ti is not None else (0.0, 0.0)
                            n = normales[ni] if ni is not None else normal_cara
                            destino.extend((p[0], p[1], p[2], uv[0], uv[1], n[0], n[1], n[2]))

        for mat, lista in datos.items():
            if lista and mat not in self.excluir_materiales:
                self._datos[mat] = np.array(lista, dtype=np.float32).reshape(-1, FLOATS_POR_VERTICE)

    @staticmethod
    def _normal_cara(a, b, c):
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        largo = math.sqrt(sum(x * x for x in n))
        if largo == 0:
            return (0.0, 1.0, 0.0)
        return tuple(x / largo for x in n)

    # ------------------------------------------------------------- Texturas
    @staticmethod
    def _cargar_textura(ruta):
        ruta = os.path.abspath(ruta)
        if ruta in _cache_texturas:
            return _cache_texturas[ruta]

        img = pygame.image.load(ruta)
        if pygame.display.get_surface() is not None:
            img = img.convert_alpha()
        # Se sube la imagen con la fila superior primero: las UV de los modelos
        # (retratos, etc.) fueron ajustadas para esta orientación.
        if hasattr(pygame.image, 'tobytes'):
            data = pygame.image.tobytes(img, 'RGBA', False)
        else:
            data = pygame.image.tostring(img, 'RGBA', False)
        w, h = img.get_size()

        alfa = np.frombuffer(data, dtype=np.uint8)[3::4]
        transparente = bool(alfa.size) and int(alfa.min()) < 250

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        try:
            glGenerateMipmap(GL_TEXTURE_2D)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        except Exception:
            # Drivers antiguos sin glGenerateMipmap
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        try:
            # Filtrado anisotrópico: el suelo y las paredes se ven nítidos a distancia
            max_aniso = glGetFloatv(_GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT)
            glTexParameterf(GL_TEXTURE_2D, _GL_TEXTURE_MAX_ANISOTROPY_EXT, min(8.0, float(max_aniso)))
        except Exception:
            pass
        glBindTexture(GL_TEXTURE_2D, 0)

        _cache_texturas[ruta] = (tex_id, transparente)
        return _cache_texturas[ruta]

    def _load_textures(self, base_path):
        for mat, m in self.materiales.items():
            if not m['textura']:
                continue
            tex_path = os.path.join(base_path, m['textura'])
            if os.path.exists(tex_path):
                m['tex_id'], m['transparente'] = self._cargar_textura(tex_path)
            elif mat in self._datos:
                print(f"⚠️ Textura no encontrada: {tex_path} (se usará el color del material)")

    # ----------------------------------------------------------------- VBOs
    def _generate_vbos(self):
        for mat, arr in self._datos.items():
            self.vbos[mat] = (vbo.VBO(arr), len(arr))
            self.bounding_boxes[mat] = (arr[:, 0:3].min(axis=0).tolist(), arr[:, 0:3].max(axis=0).tolist())
        self._datos = {}

    # ------------------------------------------------------------ Colisión
    def _load_collision_mesh(self, ruta_col):
        verts = []
        with open(ruta_col, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('v '):
                    verts.append([float(x) for x in line.split()[1:4]])
                elif line.startswith('f '):
                    idx = [_indice_obj(p.split('/')[0], len(verts)) for p in line.split()[1:]]
                    for k in range(1, len(idx) - 1):
                        a, b, c = verts[idx[0]], verts[idx[k]], verts[idx[k + 1]]
                        minx, maxx = int(min(a[0], b[0], c[0]) // self.cell_size), int(max(a[0], b[0], c[0]) // self.cell_size)
                        minz, maxz = int(min(a[2], b[2], c[2]) // self.cell_size), int(max(a[2], b[2], c[2]) // self.cell_size)
                        for cx in range(minx, maxx + 1):
                            for cz in range(minz, maxz + 1):
                                self.collision_cells[(cx, cz)].append((a, b, c))

    def _point_in_tri(self, p, a, b, c):
        # Test basado en coordenadas baricéntricas y distancia al plano
        def v(u, w): return [w[i] - u[i] for i in range(3)]
        def dot(u, w): return sum(u[i] * w[i] for i in range(3))
        def cross(u, w): return [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
        ab, ac = v(a, b), v(a, c)
        n = cross(ab, ac)
        ln = math.sqrt(dot(n, n))
        if ln == 0:
            return False
        normal = [x / ln for x in n]
        dist = dot(v(a, p), normal)
        proj = [p[i] - dist * normal[i] for i in range(3)]
        v0, v1, v2 = v(a, c), v(a, b), v(a, proj)
        d00, d01 = dot(v0, v0), dot(v0, v1)
        d02, d11 = dot(v0, v2), dot(v1, v1)
        d12 = dot(v1, v2)
        denom = d00 * d11 - d01 * d01
        if denom == 0:
            return False
        u = (d11 * d02 - d01 * d12) / denom
        w = (d00 * d12 - d01 * d02) / denom
        return u >= 0 and w >= 0 and u + w <= 1 and abs(dist) <= self.collision_radius

    def collides(self, point):
        cx, cz = int(point[0] // self.cell_size), int(point[2] // self.cell_size)
        for tri in self.collision_cells.get((cx, cz), []):
            if self._point_in_tri(point, *tri):
                return True
        return False

    def _in_frustum(self, bb):
        # Simplificado: distancia al centro del AABB
        min_bb, max_bb = bb
        center = [(min_bb[i] + max_bb[i]) / 2 for i in range(3)]
        dist = math.sqrt(sum(c ** 2 for c in center))
        return dist < self.culling_distance

    @classmethod
    def desde_datos(cls, datos, colores, culling_dist=1e9):
        """Crea un modelo a partir de geometría ya armada en memoria.
        datos: material -> array (N, 8) [posición, uv, normal]; colores: material -> (r, g, b)."""
        m = cls(None, None, culling_dist=culling_dist)
        for mat, color in colores.items():
            m.materiales[mat] = _material_defecto()
            m.materiales[mat]['kd'] = list(color)
            m.materiales[mat]['ks'] = [0.08, 0.08, 0.08]
        m._datos = {k: np.ascontiguousarray(v, dtype=np.float32) for k, v in datos.items() if len(v)}
        m._generate_vbos()
        return m

    # --------------------------------------------------------------- Carga
    def cargarmodelos(self):
        _verificar_archivo(self.path_obj)
        _verificar_archivo(self.path_mtl)

        base = os.path.dirname(self.path_obj)
        self._load_mtl(self.path_mtl)
        self._load_obj(self.path_obj)
        self._load_textures(base)
        self._generate_vbos()

        if self.path_colision:
            try:
                _verificar_archivo(self.path_colision)
                self._load_collision_mesh(self.path_colision)
            except (FileNotFoundError, RuntimeError) as e:
                print(f"⚠️ Colisiones desactivadas: {e}")

    def liberar(self):
        """Libera los buffers de la GPU. Llamar antes de cerrar pygame para evitar
        los mensajes de PyOpenGL al apagar Python."""
        for vb, _ in self.vbos.values():
            try:
                vb.delete()
            except Exception:
                pass
        self.vbos.clear()

    # -------------------------------------------------------------- Dibujo
    def draw(self):
        glEnable(GL_LIGHTING)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)

        for mat, (vb, count) in self.vbos.items():
            if not self._in_frustum(self.bounding_boxes[mat]):
                continue

            m = self.materiales.get(mat) or _material_defecto()
            tex = m['tex_id']
            _iluminacion.set_modo(self.modos.get(mat, _iluminacion.MODO_NORMAL))

            glEnable(GL_TEXTURE_2D)
            alfa = m.get('alfa', 1.0)       # < 1 para materiales translúcidos (vidrio)
            if tex:
                glBindTexture(GL_TEXTURE_2D, tex)
                glColor4f(1.0, 1.0, 1.0, alfa)
            else:
                glBindTexture(GL_TEXTURE_2D, textura_blanca())
                glColor4f(m['kd'][0], m['kd'][1], m['kd'][2], alfa)

            # Hojas, plantas y otras texturas con transparencia
            if tex and m['transparente']:
                glEnable(GL_ALPHA_TEST)
                glAlphaFunc(GL_GREATER, 0.5)
            else:
                glDisable(GL_ALPHA_TEST)

            # Brillo especular sutil (los valores de Blender son demasiado altos para OpenGL fijo)
            spec = [min(s, 0.5) * 0.3 for s in m['ks']] + [1.0]
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, spec)
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, max(4.0, min(64.0, m['ns'] / 8.0)))

            transformar_uv = m['escala_uv'] != (1.0, 1.0) or m['offset_uv'] != (0.0, 0.0)
            if transformar_uv:
                glMatrixMode(GL_TEXTURE)
                glPushMatrix()
                glLoadIdentity()
                glTranslatef(m['offset_uv'][0], m['offset_uv'][1], 0.0)
                glScalef(m['escala_uv'][0], m['escala_uv'][1], 1.0)
                glMatrixMode(GL_MODELVIEW)

            vb.bind()
            glVertexPointer(3, GL_FLOAT, STRIDE, vb)
            glTexCoordPointer(2, GL_FLOAT, STRIDE, vb + 12)
            glNormalPointer(GL_FLOAT, STRIDE, vb + 20)
            glDrawArrays(GL_TRIANGLES, 0, count)
            vb.unbind()

            if transformar_uv:
                glMatrixMode(GL_TEXTURE)
                glPopMatrix()
                glMatrixMode(GL_MODELVIEW)

        _iluminacion.set_modo(_iluminacion.MODO_NORMAL)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisable(GL_ALPHA_TEST)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
