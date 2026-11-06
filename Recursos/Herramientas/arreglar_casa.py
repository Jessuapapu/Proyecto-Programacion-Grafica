# arregla las coordenadas de textura de la casa (Hacienda.obj)
# - techo: tejas del mismo tamaño en todas las caras y alineadas con la pendiente
# - parte de abajo del alero: tablas de madera (material nuevo "Cielo")
# - paredes, piso, vigas, columnas y barandas: proyeccion por caja, sin estirar la textura
# - quita caras repetidas de las paredes (parpadeaban) y voltea las que miraban al lado equivocado
# - endereza el techo (esquinas repetidas y cumbrera torcida) y le pone caballetes de teja
# - endereza la mesa que estaba de lado (tambien en la malla de colision) y le pone textura al rifle del piso
# se puede correr varias veces, siempre da el mismo resultado
# uso: python Recursos/Herramientas/arreglar_casa.py
import os
import numpy as np

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CARPETA = os.path.join(RAIZ, "modelosObj", "Hacienda")
OBJ = os.path.join(CARPETA, "Hacienda.obj")
MTL = os.path.join(CARPETA, "Hacienda.mtl")

TEJA_U, TEJA_V = 24.0, 12.8          # unidades del mundo por cada repeticion de techo_teja.jpg
MADERA = 5.0                         # repeticion de Madera.jpeg a lo largo de la veta
PARED = 4.0                          # repeticion de pared_cal.jpg
PISO = 4.0
MADERAS = ("Soporte", "Cercado2", "Acercado", "Partedeltecho")

# techo a cuatro aguas: esquinas del alero y extremos de la cumbrera
ALERO_Y, CUMBRERA_Y = 10.85, 22.2
X0, X1, Z0, Z1 = -17.33, 31.47, -39.98, 29.88
XC = (X0 + X1) / 2
TECHO = {194: (X0, ALERO_Y, Z1), 195: (X0, ALERO_Y, Z1), 196: (X0, ALERO_Y, Z0), 197: (X0, ALERO_Y, Z0),
         198: (X1, ALERO_Y, Z1), 200: (X1, ALERO_Y, Z0),
         199: (XC, CUMBRERA_Y, Z1 - 18.0), 201: (XC, CUMBRERA_Y, Z0 + 18.0)}


def leer():
    lineas = [l.rstrip("\r") for l in open(OBJ, encoding="utf-8", errors="ignore").read().split("\n")]
    V, T = [], []
    for l in lineas:
        if l.startswith("v "):
            V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith("vt "):
            T.append([float(x) for x in l.split()[1:3]])
    return lineas, np.array(V), T


def caras(lineas):
    # devuelve [(n_linea, material, [(v, vt, vn), ...])]
    mat, out = None, []
    for k, l in enumerate(lineas):
        if l.startswith("usemtl"):
            mat = l.split()[1]
        elif l.startswith("f "):
            vs = []
            for p in l.split()[1:]:
                partes = (p.split("/") + ["", ""])[:3]
                vs.append(tuple(int(x) if x else 0 for x in partes))
            out.append((k, mat, vs))
    return out


def normal(P):
    n = np.cross(P[1] - P[0], P[2] - P[0])
    return n / (np.linalg.norm(n) + 1e-12)


def componentes(lista, V):
    # piezas sueltas (cada tabla, columna o poste) para saber su eje largo
    padre = {}

    def raiz(a):
        while padre.setdefault(a, a) != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a
    for _, _, vs in lista:
        for v, _, _ in vs[1:]:
            padre[raiz(v)] = raiz(vs[0][0])
    grupos = {}
    for _, _, vs in lista:
        grupos.setdefault(raiz(vs[0][0]), set()).update(v for v, _, _ in vs)
    eje = {}
    for r, s in grupos.items():
        p = V[[i - 1 for i in s]]
        eje[r] = int(np.argmax(p.max(0) - p.min(0)))
    return {v: eje[raiz(v)] for _, _, vs in lista for v, _, _ in vs}


def caja(P, n, escala_u, escala_v, eje_largo=None):
    # proyeccion por caja: se usan los dos ejes que no son el de la normal
    k = int(np.argmax(np.abs(n)))
    otros = [i for i in range(3) if i != k]
    if eje_largo in otros:
        otros = [eje_largo] + [i for i in otros if i != eje_largo]
    elif 1 in otros:
        otros = [i for i in otros if i != 1] + [1]      # en paredes v va hacia arriba
    return [(p[otros[0]] / escala_u, p[otros[1]] / escala_v) for p in P]


def enderezar_techo(lineas, V):
    # mueve los 8 vertices del techo a su lugar (antes habia esquinas repetidas un poco corridas)
    n = 0
    for k, l in enumerate(lineas):
        if l.startswith("v "):
            n += 1
            if n in TECHO:
                x, y, z = TECHO[n]
                lineas[k] = f"v {x:.6f} {y:.6f} {z:.6f}"
                V[n - 1] = (x, y, z)


def caballetes(n_v, n_vt):
    # tejas de cumbrera: medio tubo sobre la cumbrera y las 4 limatesas
    p = {i: np.array(c) for i, c in TECHO.items()}
    lineas_t = [(p[199], p[201]), (p[199], p[194]), (p[199], p[198]), (p[201], p[196]), (p[201], p[200])]
    vs, vts, fs = [], [], []
    lados, radio = 6, 0.38
    for a, b in lineas_t:
        eje = b - a
        largo = np.linalg.norm(eje)
        eje /= largo
        arriba = np.array([0.0, 1.0, 0.0]) - eje * eje[1]
        arriba /= np.linalg.norm(arriba)
        lado = np.cross(eje, arriba)
        base_v = n_v + len(vs) + 1
        base_t = n_vt + len(vts) + 1
        for extremo, s in ((a, 0.0), (b, largo)):
            for j in range(lados + 1):
                ang = np.pi * j / lados
                q = extremo + (lado * np.cos(ang) + arriba * np.sin(ang)) * radio + arriba * 0.08
                vs.append(q)
                vts.append((j / lados * 0.035, s / TEJA_V))
        for j in range(lados):
            i0, i1 = j, j + 1
            k0, k1 = j + lados + 1, j + lados + 2
            fs.append(((base_v + i0, base_t + i0), (base_v + k0, base_t + k0), (base_v + k1, base_t + k1)))
            fs.append(((base_v + i0, base_t + i0), (base_v + k1, base_t + k1), (base_v + i1, base_t + i1)))
    out = ["o Cumbrera", "usemtl Techo", "s 0"]
    out += [f"v {q[0]:.5f} {q[1]:.5f} {q[2]:.5f}" for q in vs]
    out += [f"vt {u:.5f} {v:.5f}" for u, v in vts]
    out += ["f " + " ".join(f"{v}/{t}" for v, t in f) for f in fs]
    return out


def main():
    lineas, V, T = leer()
    # quitar caballetes de una corrida anterior (siempre van al final)
    if "o Cumbrera" in lineas:
        corte = lineas.index("o Cumbrera")
        lineas = lineas[:corte]
        V = V[:sum(1 for l in lineas if l.startswith("v "))]
        T = T[:sum(1 for l in lineas if l.startswith("vt "))]
    enderezar_techo(lineas, V)
    lista = caras(lineas)
    ejes = componentes([c for c in lista if c[1] in MADERAS], V)
    nuevos_vt = []
    borrar = set()
    vistas = set()
    material_cielo = {}

    def agregar_uv(uvs):
        base = len(T) + len(nuevos_vt) + 1
        nuevos_vt.extend(uvs)
        return list(range(base, base + len(uvs)))

    # paredes verticales: la normal tiene que salir del muro, no meterse en el
    paredes = []
    for k, mat, vs in lista:
        if mat == "Paredes":
            P = np.array([V[v - 1] for v, _, _ in vs])
            paredes.append((k, P, normal(P)))
    voltear = set()
    for k, P, n in paredes:
        if abs(n[1]) > 0.5:
            continue
        c = P.mean(0)
        for k2, P2, n2 in paredes:
            if k2 == k or abs(np.dot(n, n2)) < 0.95:
                continue
            d = np.dot(P2[0] - c, n)            # distancia a la otra cara, del lado de la normal
            if not 0.05 < abs(d) < 0.45:
                continue
            q = c + n * d                        # el centro proyectado tiene que caer dentro de la otra cara
            lo, hi = P2.min(0) - 0.01, P2.max(0) + 0.01
            if np.all(q >= lo) and np.all(q <= hi):
                if d > 0:
                    voltear.add(k)               # el muro esta del lado de la normal
                break

    for k, mat, vs in lista:
        P = np.array([V[v - 1] for v, _, _ in vs])
        n = normal(P)
        if mat == "Paredes" and k in voltear:
            vs = vs[::-1]
            P = P[::-1]
            n = -n
        if mat == "Paredes":
            vs = [(v, t, 0) for v, t, _ in vs]     # sin vn: el juego calcula la normal con el orden
            clave = tuple(sorted(tuple(p) for p in P.round(3)))
            if clave in vistas:
                borrar.add(k)
                continue
            vistas.add(clave)
            uvs = caja(P, n, PARED, PARED * 1104 / 736)
        elif mat == "Techo" or mat == "Cielo":
            if len({tuple(p) for p in P.round(4)}) < 3:
                borrar.add(k)          # quedo aplastada al juntar las esquinas repetidas
                continue
            vs = [(v, t, 0) for v, t, _ in vs]
            n = normal(P)
            if n[1] > 0.2:
                # tejas: v sube por la pendiente, u va a lo largo del alero
                arriba = np.array([0.0, 1.0, 0.0]) - n * n[1]
                arriba /= np.linalg.norm(arriba)
                lado = np.cross(arriba, n)
                uvs = [(p @ lado / TEJA_U, p @ arriba / TEJA_V) for p in P]
            else:
                # debajo del alero: tablas de madera
                material_cielo[k] = True
                uvs = caja(P, n, MADERA, MADERA * 1004 / 736, eje_largo=0)
        elif mat == "Suelo":
            uvs = caja(P, n, PISO, PISO)
        elif mat in MADERAS:
            uvs = caja(P, n, MADERA, MADERA * 1004 / 736, eje_largo=ejes[vs[0][0]])
        else:
            continue
        ids = agregar_uv(uvs)
        lineas[k] = "f " + " ".join(f"{v}/{t}/{vn}" if vn else f"{v}/{t}" for (v, _, vn), t in zip(vs, ids))

    # caras de abajo del techo pasan al material Cielo
    salida = []
    mat_actual = None
    for k, l in enumerate(lineas):
        if k in borrar:
            continue
        if l.startswith("usemtl"):
            mat_actual = l.split()[1]
            salida.append(l)
            continue
        if l.startswith("f ") and mat_actual in ("Techo", "Cielo"):
            quiere = "Cielo" if k in material_cielo else "Techo"
            if quiere != mat_actual:
                salida.append("usemtl " + quiere)
                mat_actual = quiere
        salida.append(l)

    # los vt nuevos van antes de la primera cara (el juego lee el archivo en orden y las
    # caras usan indices globales: los vt viejos que estan antes siguen con su numero)
    primera_f = next(i for i, l in enumerate(salida) if l.startswith("f "))
    vt_antes = sum(1 for l in salida[:primera_f] if l.startswith("vt "))
    if vt_antes != len(T):
        # hay vt viejos despues de la primera cara: se mueven todos arriba en el mismo orden
        viejos = [l for l in salida if l.startswith("vt ")]
        salida = [l for l in salida if not l.startswith("vt ")]
        primera_f = next(i for i, l in enumerate(salida) if l.startswith("f "))
        salida[primera_f:primera_f] = viejos
        primera_f += len(viejos)
    salida[primera_f:primera_f] = [f"vt {u:.5f} {v:.5f}" for u, v in nuevos_vt]

    # si se corre otra vez, los vt viejos que ya no usa nadie se quitan
    usados = set()
    for l in salida:
        if l.startswith("f "):
            for p in l.split()[1:]:
                partes = p.split("/")
                if len(partes) > 1 and partes[1]:
                    usados.add(int(partes[1]))
    mapa, nuevo, idx, limpio = {}, 0, 0, []
    for l in salida:
        if l.startswith("vt "):
            idx += 1
            if idx in usados:
                nuevo += 1
                mapa[idx] = nuevo
                limpio.append(l)
            continue
        limpio.append(l)
    final = []
    for l in limpio:
        if l.startswith("f "):
            partes = []
            for p in l.split()[1:]:
                s = p.split("/")
                if len(s) > 1 and s[1]:
                    s[1] = str(mapa[int(s[1])])
                partes.append("/".join(s))
            l = "f " + " ".join(partes)
        final.append(l)
    n_v = sum(1 for l in final if l.startswith("v "))
    n_vt = sum(1 for l in final if l.startswith("vt "))
    final = [l for l in final if l != ""] + caballetes(n_v, n_vt) + [""]
    open(OBJ, "w", encoding="utf-8").write("\n".join(final))

    # material nuevo para la parte de abajo del alero
    mtl = open(MTL, encoding="utf-8").read()
    bloques = mtl.split("newmtl ")
    for i, b in enumerate(bloques):
        if b.startswith("Partedeltecho"):
            bloques[i] = b.replace("map_Kd pared_cal.jpg", "map_Kd Madera.jpeg")
    mtl = "newmtl ".join(bloques)
    if "newmtl Cielo" not in mtl:
        mtl = mtl.rstrip("\n") + ("\n\nnewmtl Cielo\nNs 20.000000\nKa 1.000000 1.000000 1.000000\n"
                                  "Kd 0.800000 0.800000 0.800000\nKs 0.100000 0.100000 0.100000\n"
                                  "Ke 0.000000 0.000000 0.000000\nNi 1.450000\nd 1.000000\nillum 2\n"
                                  "map_Kd Madera.jpeg\n")
    open(MTL, "w", encoding="utf-8").write(mtl)
    print(f"caras repetidas quitadas: {len(borrar)}, uv nuevas: {len(nuevos_vt)}, "
          f"caras bajo el alero: {len(material_cielo)}")


def enderezar_mesa():
    # la mesa de la esquina estaba acostada de lado (tablero vertical y patas horizontales)
    ruta = os.path.join(RAIZ, "modelosObj", "Mesas", "Mesas.obj")
    lineas = [l.rstrip("\r") for l in open(ruta, encoding="utf-8", errors="ignore").read().split("\n")]
    pos = [(k, np.array([float(x) for x in l.split()[1:4]])) for k, l in enumerate(lineas) if l.startswith("v ")]
    mesa = [(i, k, p) for i, (k, p) in enumerate(pos) if p[0] > 12.0]
    P = np.array([p for _, _, p in mesa])
    if np.ptp(P[:, 1]) < np.ptp(P[:, 2]):
        print("la mesa ya esta derecha")
        return
    # girar 90 grados en x: las patas (+z) quedan hacia abajo (-y)
    c = P.mean(0)
    Q = P - c
    Q = np.stack([Q[:, 0], -Q[:, 2], Q[:, 1]], 1)
    Q = Q - [0, Q[:, 1].min(), 0] + [c[0], -2.3, 15.4]
    Q[:, 0] += -Q[:, 0].mean() + c[0]
    ids = set()
    for (i, k, _), q in zip(mesa, Q):
        lineas[k] = f"v {q[0]:.6f} {q[1]:.6f} {q[2]:.6f}"
        ids.add(i + 1)
    # sus normales viejas ya no sirven: se calculan de nuevo por cara
    for k, l in enumerate(lineas):
        if l.startswith("f ") and int(l.split()[1].split("/")[0]) in ids:
            lineas[k] = "f " + " ".join("/".join(p.split("/")[:2]) for p in l.split()[1:])
    open(ruta, "w", encoding="utf-8").write("\n".join(lineas))
    print("mesa enderezada")


def textura_rifle():
    # el mtl del rifle apuntaba a una ruta de la compu donde se hizo el modelo
    ruta = os.path.join(RAIZ, "modelosObj", "Arbolitos", "arbolito3.mtl")
    s = open(ruta, encoding="utf-8").read()
    s2 = s.replace("C:/Users/User/OneDrive/Documentos/Blender/k98_texture1.png", "k98_texture1.png")
    if s2 != s:
        open(ruta, "w", encoding="utf-8").write(s2)
    destino = os.path.join(RAIZ, "modelosObj", "Arbolitos", "k98_texture1.png")
    if not os.path.exists(destino):
        import shutil
        shutil.copy(os.path.join(RAIZ, "modelosObj", "Pistolas", "k98_texture1.png"), destino)


def colision_mesa():
    # la malla de colision todavia tenia la mesa acostada: se cambia por la mesa derecha
    ruta = os.path.join(RAIZ, "modelosObj", "colision_hacienda.obj")
    lineas = [l.rstrip("\r") for l in open(ruta, encoding="utf-8", errors="ignore").read().split("\n")]
    if "o MesaDerecha" in lineas:
        lineas = lineas[:lineas.index("o MesaDerecha")]
    V = [np.array([float(x) for x in l.split()[1:4]]) for l in lineas if l.startswith("v ")]
    lo, hi = np.array([13.7, -2.6, 13.0]), np.array([21.0, 2.3, 17.8])
    salida, quitadas = [], 0
    for l in lineas:
        if l.startswith("f "):
            ids = [int(x.split("/")[0]) for x in l.split()[1:]]
            if all(np.all(V[i - 1] >= lo) and np.all(V[i - 1] <= hi) for i in ids):
                quitadas += 1
                continue
        salida.append(l)
    while salida and salida[-1] == "":
        salida.pop()
    # mesa derecha desde Mesas.obj
    mesa = os.path.join(RAIZ, "modelosObj", "Mesas", "Mesas.obj")
    mv, mf = [], []
    for l in open(mesa, encoding="utf-8", errors="ignore"):
        if l.startswith("v "):
            mv.append([float(x) for x in l.split()[1:4]])
        elif l.startswith("f "):
            mf.append([int(x.split("/")[0]) for x in l.split()[1:]])
    usados = sorted({i for f in mf for i in f if mv[i - 1][0] > 12.0})
    nuevo = {i: len(V) + k + 1 for k, i in enumerate(usados)}
    salida.append("o MesaDerecha")
    salida += [f"v {mv[i - 1][0]:.6f} {mv[i - 1][1]:.6f} {mv[i - 1][2]:.6f}" for i in usados]
    salida += ["f " + " ".join(str(nuevo[i]) for i in f) for f in mf if all(i in nuevo for i in f)]
    open(ruta, "w", encoding="utf-8").write("\n".join(salida) + "\n")
    print(f"colision: caras de la mesa vieja quitadas {quitadas}")


if __name__ == "__main__":
    main()
    enderezar_mesa()
    textura_rifle()
    colision_mesa()
