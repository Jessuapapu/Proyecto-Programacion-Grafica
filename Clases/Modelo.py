import os
import pygame
from OpenGL.GL import *
from OpenGL.arrays import vbo
import numpy as np
import math
from collections import defaultdict

class Modelos:
    def __init__(self, path_obj, path_mtl, path_colision=None, culling_dist=300.0, cell_size=4.0, collision_radius=0.6):
        # Datos de geometría y texturas
        self.vertices = []
        self.texcoords = []
        self.groups = {}              # material -> listas de caras
        self.material_files = {}      # material -> nombre de archivo de textura
        self.textures_gl = {}         # material -> ID textura OpenGL
        self.vbos = {}                # material -> (VBO, count)
        self.bounding_boxes = {}      # material -> (min, max)

        self.path_obj = path_obj
        self.path_mtl = path_mtl
        self.path_colision = path_colision
        
        # Parámetros de colisión y culling
        self.collision_cells = defaultdict(list)
        self.cell_size = cell_size
        self.collision_radius = collision_radius
        self.culling_distance = culling_dist

    def _load_mtl(self, ruta_mtl):
        current = None
        with open(ruta_mtl, 'r') as f:
            for line in f:
                if line.startswith('newmtl'):
                    current = line.split()[1]
                elif line.startswith('map_Kd') and current:
                    tex = os.path.basename(line.split()[-1])
                    self.material_files[current] = tex

    def _load_obj(self, ruta_obj):
        current = None
        with open(ruta_obj, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    parts = line.strip().split()[1:]
                    self.vertices.append([float(x) for x in parts])
                elif line.startswith('vt '):
                    parts = line.strip().split()[1:]
                    self.texcoords.append([float(x) for x in parts])
                elif line.startswith('usemtl '):
                    current = line.split()[1]
                    self.groups.setdefault(current, [])
                elif line.startswith('f '):
                    face = []
                    for vert in line.strip().split()[1:]:
                        v, vt = (vert.split('/') + [0,0])[:2]
                        face.append((int(v)-1, int(vt)-1))
                    self.groups[current].append(face)

    def _load_textures(self, base_path):
        glEnable(GL_TEXTURE_2D)
        
        for mat, filename in self.material_files.items():
            tex_path = os.path.join(base_path, filename)
            if os.path.exists(tex_path):
                img = pygame.image.load(tex_path)
                img = pygame.transform.flip(img, False, True)  # Corrige orientación
                img = img.convert_alpha()
                data = pygame.image.tostring(img, 'RGBA', True)
                w, h = img.get_size()
                tex_id = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, tex_id)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
                glGenerateMipmap(GL_TEXTURE_2D)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                self.textures_gl[mat] = tex_id
            else:
                print(f"⚠️ Textura no encontrada: {tex_path}")


    def _generate_vbos(self):
        for mat, faces in self.groups.items():
            data = []
            min_bb = [math.inf]*3
            max_bb = [-math.inf]*3
            for face in faces:
                for v_idx, vt_idx in face:
                    vert = self.vertices[v_idx]
                    uv = self.texcoords[vt_idx] if vt_idx < len(self.texcoords) else [0.0,0.0]
                    data.extend(vert + uv)
                    for i in range(3):
                        min_bb[i] = min(min_bb[i], vert[i])
                        max_bb[i] = max(max_bb[i], vert[i])
            arr = np.array(data, dtype=np.float32)
            buffer = vbo.VBO(arr)
            self.vbos[mat] = (buffer, len(faces)*3)
            self.bounding_boxes[mat] = (min_bb, max_bb)

    def _load_collision_mesh(self, ruta_col):
        verts = []
        with open(ruta_col, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    verts.append([float(x) for x in line.strip().split()[1:]])
                elif line.startswith('f '):
                    idx = [int(p.split('/')[0]) -1 for p in line.strip().split()[1:]]
                    if len(idx)==3:
                        a,b,c = [verts[i] for i in idx]
                        minx,maxx = int(min(a[0],b[0],c[0])//self.cell_size), int(max(a[0],b[0],c[0])//self.cell_size)
                        minz,maxz = int(min(a[2],b[2],c[2])//self.cell_size), int(max(a[2],b[2],c[2])//self.cell_size)
                        for cx in range(minx, maxx+1):
                            for cz in range(minz, maxz+1):
                                self.collision_cells[(cx,cz)].append((a,b,c))

    def _point_in_tri(self, p, a,b,c):
        # Test basado en barycentric y distancia al plano
        def v(u,v): return [v[i]-u[i] for i in range(3)]
        def dot(u,v): return sum(u[i]*v[i] for i in range(3))
        def cross(u,v): return [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        def norm(v): return math.sqrt(dot(v,v))
        ab, ac = v(a,b), v(a,c)
        n = cross(ab,ac)
        ln = norm(n)
        if ln==0: return False
        normal = [x/ln for x in n]
        ap = v(a,p)
        dist = dot(ap, normal)
        proj = [p[i] - dist*normal[i] for i in range(3)]
        v0,v1,v2 = v(a,c), v(a,b), v(a,proj)
        d00,d01 = dot(v0,v0), dot(v0,v1)
        d02,d11 = dot(v0,v2), dot(v1,v1)
        d12    = dot(v1,v2)
        denom = d00*d11 - d01*d01
        if denom==0: return False
        u = (d11*d02 - d01*d12)/denom
        v = (d00*d12 - d01*d02)/denom
        return u>=0 and v>=0 and u+v<=1 and abs(dist)<=self.collision_radius

    def collides(self, point):
        cx,cz = int(point[0]//self.cell_size), int(point[2]//self.cell_size)
        for tri in self.collision_cells.get((cx,cz),[]):
            if self._point_in_tri(point, *tri):
                return True
        return False

    def _in_frustum(self, bb):
        # Simplificado: distancia al centro del AABB
        min_bb, max_bb = bb
        center = [(min_bb[i]+max_bb[i])/2 for i in range(3)]
        dist = math.sqrt(sum((center[i])**2 for i in range(3)))
        return dist < self.culling_distance

    def cargarmodelos(self):        
        # Carga de malla y texturas
        base = os.path.dirname(self.path_obj)
        self._load_mtl(self.path_mtl)
        self._load_obj(self.path_obj)
        self._load_textures(base)
        
        # Crear VBOs y bounding boxes
        self._generate_vbos()

        # Cargar malla de colisión si existe
        if self.path_colision:
            self._load_collision_mesh(self.path_colision)
        
        
    def draw(self):
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
    
        for mat, (vb, count) in self.vbos.items():
            bb = self.bounding_boxes[mat]
            if not self._in_frustum(bb):
                continue
            
            tex = self.textures_gl.get(mat)
            if tex:
                glBindTexture(GL_TEXTURE_2D, tex)
    
            vb.bind()
    
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)
            glEnableClientState(GL_NORMAL_ARRAY)
    
            # Normales simples hacia arriba (y=1) por cada vértice
            normals = np.array([0.0, 1.0, 0.0] * count, dtype=np.float32)
            glNormalPointer(GL_FLOAT, 0, normals)
    
            glVertexPointer(3, GL_FLOAT, 20, vb)
            glTexCoordPointer(2, GL_FLOAT, 20, vb + 12)
            glDrawArrays(GL_TRIANGLES, 0, count)
    
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_TEXTURE_COORD_ARRAY)
            glDisableClientState(GL_NORMAL_ARRAY)
    
            vb.unbind()
    
        glDisable(GL_LIGHTING)
