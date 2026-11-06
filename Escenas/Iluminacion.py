# iluminacion y ciclo de dia y noche
# sol, luna, luz de relleno, ambiente y niebla que cambian con la hora
# si la tarjeta soporta glsl se usa un shader por pixel, si no la luz fija de opengl
import math
import numpy as np
from OpenGL.GL import *

# parametros
SEGUNDOS_POR_HORA = 5.0     # 5 segundos = 1 hora, el dia completo dura 2 minutos
HORA_INICIAL = 9.0          # empieza en la mañana
HORA_SIEMPRE_DIA = 11.0     # hora para el modo siempre de dia
INTENSIDAD_SOL = 0.85
INTENSIDAD_LUNA = 0.24
NIEBLA_INICIO = 90.0
NIEBLA_FIN = 520.0
DISTANCIA_ASTROS = 200.0    # distancia del sol y la luna

SOL_MEDIODIA = (1.00, 0.96, 0.88)
SOL_HORIZONTE = (1.00, 0.56, 0.28)
COLOR_LUNA = (0.62, 0.72, 1.00)

AMBIENTE_DIA = (0.32, 0.35, 0.42)
AMBIENTE_ATARDECER = (0.32, 0.25, 0.25)
AMBIENTE_NOCHE = (0.07, 0.08, 0.14)

NIEBLA_DIA = (0.72, 0.80, 0.90)
NIEBLA_ATARDECER = (0.86, 0.58, 0.42)
NIEBLA_NOCHE = (0.03, 0.04, 0.08)

TINTE_CIELO_DIA = (1.00, 1.00, 1.00)
TINTE_CIELO_ATARDECER = (1.00, 0.76, 0.60)
TINTE_CIELO_NOCHE = (0.45, 0.50, 0.70)

# estado de cada frame (lo usan main.py y el skybox)
estado = {
    'hora': HORA_INICIAL,
    'factor_dia': 1.0,          # 0 noche, 1 dia
    'dir_sol': [0.0, 1.0, 0.0],
    'dir_luna': [0.0, -1.0, 0.0],
    'color_sol': list(SOL_MEDIODIA),
    'tinte_cielo': list(TINTE_CIELO_DIA),
    'niebla': list(NIEBLA_DIA),
}

_shader = None          # None si no hay shader


# utilidades
def _mezclar(a, b, t):
    return [a[i] + (b[i] - a[i]) * t for i in range(len(a))]


def _suavizar(e0, e1, x):
    # igual que smoothstep de glsl
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def _normalizar(v):
    largo = math.sqrt(sum(c * c for c in v)) or 1.0
    return [c / largo for c in v]


def hora_simulada(segundos):
    # hora (0 a 24) segun los segundos de juego
    return (HORA_INICIAL + segundos / SEGUNDOS_POR_HORA) % 24.0


def segundos_para_hora(hora):
    # lo contrario: segundos para llegar a esa hora
    return ((hora - HORA_INICIAL) % 24.0) * SEGUNDOS_POR_HORA


def es_de_dia():
    return estado['factor_dia'] >= 0.5


# shaders
# modos especiales del shader
MODO_NORMAL = 0
MODO_TERRENO = 1     # suelo con textura de detalle
MODO_PARED = 2       # paredes con zocalo
MODO_FOLLAJE = 3     # hojas, la luz pasa un poco
MODO_PISO = 4        # piso del corredor y baldosas

ESCALA_DETALLE = 0.2          # cada cuanto se repite el detalle del suelo
ALTURA_ZOCALO = -0.6          # altura del zocalo
COLOR_ZOCALO = (0.47, 0.53, 0.58)

# limites de la casa (x0, x1, z0, z1) y altura del techo
# adentro cambia el piso, las paredes, el techo y hay luz de lamparas
CASA = (-8.6, 23.13, -29.52, 19.54)
TECHO_CASA = 10.7
PISO_CASA = -2.2
LUZ_INTERIOR = (0.30, 0.28, 0.24)

_VERTEX_SHADER = """
#version 120
uniform mat4 vistaInversa;
varying vec3 vPosOjo;
varying vec3 vMundo;
varying vec3 vNormal;
varying vec3 vArriba;
varying vec4 vColor;
varying vec2 vUV;

void main() {
    vec4 posOjo = gl_ModelViewMatrix * gl_Vertex;
    vPosOjo = posOjo.xyz;
    vMundo  = (vistaInversa * posOjo).xyz;
    vNormal = gl_NormalMatrix * gl_Normal;
    vArriba = gl_NormalMatrix * vec3(0.0, 1.0, 0.0);
    vColor  = gl_Color;
    vUV     = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    gl_Position = gl_ProjectionMatrix * posOjo;
}
"""

_FRAGMENT_SHADER = """
#version 120
uniform sampler2D textura;
uniform sampler2D detalle;
uniform int modo;
uniform float escalaDetalle;
uniform float alturaZocalo;
uniform vec3 colorZocalo;
uniform vec4 casa;
uniform float techoCasa;
uniform float pisoCasa;
uniform vec3 luzInterior;
uniform mat4 vistaInversa;
varying vec3 vPosOjo;
varying vec3 vMundo;
varying vec3 vNormal;
varying vec3 vArriba;
varying vec4 vColor;
varying vec2 vUV;

float dentroCasa(vec3 p, float margen) {
    return (p.x > casa.x - margen && p.x < casa.y + margen &&
            p.z > casa.z - margen && p.z < casa.w + margen && p.y < techoCasa + 0.05) ? 1.0 : 0.0;
}

void main() {
    vec4 tex = texture2D(textura, vUV);
    vec4 base = vColor * tex;

    vec3 N = normalize(vNormal);
    if (!gl_FrontFacing) N = -N;
    vec3 Nmundo = normalize(mat3(vistaInversa) * N);
    float interior = dentroCasa(vMundo, -0.05);

    if (modo == 1) {
        // suelo: textura de color por el detalle en dos escalas
        // en el alfa va cuanto pasto hay
        vec2 p = vMundo.xz * escalaDetalle;
        vec3 d1 = texture2D(detalle, p).rgb;
        vec3 d2 = texture2D(detalle, p * 0.27 + vec2(0.37, 0.71)).rgb;
        float pasto = d1.r * 0.6 + d2.r * 0.4;
        float tierra = d1.g * 0.6 + d2.g * 0.4;
        float det = mix(tierra, pasto, tex.a) * 2.0;
        base = vec4(vColor.rgb * tex.rgb * det, 1.0);
    } else if (modo == 2) {
        float lum = dot(tex.rgb, vec3(0.333));
        // distancia a cada borde de la casa
        float b0 = vMundo.x - casa.x, b1 = casa.y - vMundo.x, b2 = vMundo.z - casa.z, b3 = casa.w - vMundo.z;
        float borde = min(min(b0, b1), min(b2, b3));
        float haciaCentro;
        if (abs(Nmundo.y) > 0.7) {
            // techo y piso solo cuentan como interior adentro de las paredes
            haciaCentro = step(0.34, min(b0, b1)) * step(0.02, min(b2, b3));
        } else if (borde > 0.6) {
            haciaCentro = 1.0;          // tabiques
        } else {
            // cerca de una pared de afuera solo es interior si mira hacia adentro
            // (asi los marcos de puertas y ventanas quedan como exterior)
            float adentro = -1.0;
            if (b0 < 0.6) adentro = max(adentro, Nmundo.x);
            if (b1 < 0.6) adentro = max(adentro, -Nmundo.x);
            if (b2 < 0.6) adentro = max(adentro, Nmundo.z);
            if (b3 < 0.6) adentro = max(adentro, -Nmundo.z);
            haciaCentro = step(0.5, adentro);
        }
        interior = dentroCasa(vMundo, 0.15) * haciaCentro;
        if (interior > 0.5 && Nmundo.y < -0.7) {
            // techo de vigas y caña
            float viga = step(fract(vMundo.z / 3.2), 0.11);
            float cana = step(0.5, fract(vMundo.x * 5.0));
            vec3 colorCana = mix(vec3(0.60, 0.46, 0.30), vec3(0.50, 0.37, 0.23), cana);
            base.rgb = mix(colorCana, vec3(0.32, 0.18, 0.10), viga) * (0.85 + 0.3 * lum);
        } else if (interior > 0.5) {
            // pared blanca con rodapie
            if (vMundo.y < pisoCasa + 0.55) base.rgb = vec3(0.60, 0.31, 0.21) * (0.85 + 0.3 * lum);
        } else if (vMundo.y < alturaZocalo) {
            // afuera: zocalo y una linea de sombra
            base.rgb = colorZocalo * (0.78 + 0.32 * lum);
        } else if (vMundo.y < alturaZocalo + 0.15) {
            base.rgb *= 0.72;
        }
    } else if (modo == 4 && interior > 0.5) {
        // baldosas con juntas
        vec2 t = vMundo.xz / 1.35;
        vec2 c = floor(t);
        vec2 f = fract(t);
        float h = fract(sin(dot(c, vec2(12.9898, 78.233))) * 43758.5453);
        vec3 barro = mix(vec3(0.50, 0.27, 0.19), vec3(0.62, 0.35, 0.24), h);
        float lum = dot(tex.rgb, vec3(0.333)) / 0.5;
        float junta = step(0.035, f.x) * step(0.035, f.y) * step(f.x, 0.965) * step(f.y, 0.965);
        base.rgb = mix(vec3(0.50, 0.45, 0.40), barro * (0.9 + 0.15 * lum), junta);
    }

    vec3 V = normalize(-vPosOjo);

    // lo que mira al cielo recibe mas luz
    float h = dot(N, normalize(vArriba)) * 0.5 + 0.5;
    float follaje = (modo == 3) ? 1.0 : 0.0;
    vec3 luz = gl_LightModel.ambient.rgb * mix(mix(0.68, 0.95, follaje), 1.15, h);
    float envoltura = 0.55 * follaje;
    vec3 brillo = vec3(0.0);

    for (int i = 0; i < 3; i++) {
        vec3 L = normalize(gl_LightSource[i].position.xyz);
        float NdotL = max(dot(N, L), 0.0);
        luz += gl_LightSource[i].diffuse.rgb * max((dot(N, L) + envoltura) / (1.0 + envoltura), 0.0);
        if (NdotL > 0.0) {
            vec3 H = normalize(L + V);
            brillo += gl_LightSource[i].specular.rgb *
                      pow(max(dot(N, H), 0.0), gl_FrontMaterial.shininess);
        }
    }

    // las hojas dejan pasar un poco de luz
    luz += gl_LightSource[0].diffuse.rgb * 0.3 * follaje;
    // lamparas de la casa
    luz += luzInterior * interior;

    vec3 color = base.rgb * luz + brillo * gl_FrontMaterial.specular.rgb;

    // para que al mediodia no se queme la imagen
    color = color / (1.0 + 0.18 * color);
    color *= 1.12;

    // niebla
    float d = length(vPosOjo);
    float f = clamp((gl_Fog.end - d) * gl_Fog.scale, 0.0, 1.0);
    color = mix(gl_Fog.color.rgb, color, f);

    gl_FragColor = vec4(color, base.a);
}
"""

_uniformes = {}
_activo = False
_modo_actual = None


def _compilar(tipo, fuente):
    # compila un shader y tira error si falla
    sh = glCreateShader(tipo)
    glShaderSource(sh, fuente)
    glCompileShader(sh)
    if not glGetShaderiv(sh, GL_COMPILE_STATUS):
        log = glGetShaderInfoLog(sh)
        raise RuntimeError(log.decode() if isinstance(log, bytes) else str(log))
    return sh


def _crear_shader():
    # arma el programa y guarda los uniforms
    # si falla se queda con la luz fija
    global _shader
    try:
        vs = _compilar(GL_VERTEX_SHADER, _VERTEX_SHADER)
        fs = _compilar(GL_FRAGMENT_SHADER, _FRAGMENT_SHADER)
        prog = glCreateProgram()
        glAttachShader(prog, vs)
        glAttachShader(prog, fs)
        glLinkProgram(prog)
        if not glGetProgramiv(prog, GL_LINK_STATUS):
            log = glGetProgramInfoLog(prog)
            raise RuntimeError(log.decode() if isinstance(log, bytes) else str(log))
        for nombre in ("textura", "detalle", "modo", "escalaDetalle", "alturaZocalo", "colorZocalo", "vistaInversa",
                       "casa", "techoCasa", "pisoCasa", "luzInterior"):
            _uniformes[nombre] = glGetUniformLocation(prog, nombre)
        glUseProgram(prog)
        glUniform1i(_uniformes["textura"], 0)
        glUniform1i(_uniformes["detalle"], 1)
        glUniform1i(_uniformes["modo"], MODO_NORMAL)
        glUniform1f(_uniformes["escalaDetalle"], ESCALA_DETALLE)
        glUniform1f(_uniformes["alturaZocalo"], ALTURA_ZOCALO)
        glUniform3f(_uniformes["colorZocalo"], *COLOR_ZOCALO)
        glUniform4f(_uniformes["casa"], *CASA)
        glUniform1f(_uniformes["techoCasa"], TECHO_CASA)
        glUniform1f(_uniformes["pisoCasa"], PISO_CASA)
        glUniform3f(_uniformes["luzInterior"], *LUZ_INTERIOR)
        glUseProgram(0)
        _shader = prog
        print("Iluminación por píxel activada (GLSL).")
    except Exception as e:
        _shader = None
        print(f"⚠️ Shader no disponible, se usa iluminación fija de OpenGL: {e}")


def shader_disponible():
    return _shader is not None


def activar_shader():
    # llamar despues de gluLookAt
    global _activo, _modo_actual
    glEnable(GL_FOG)
    if _shader:
        glUseProgram(_shader)
        vista = np.array(glGetFloatv(GL_MODELVIEW_MATRIX), dtype=np.float64).reshape(4, 4).T
        inversa = np.linalg.inv(vista).astype(np.float32)
        glUniformMatrix4fv(_uniformes["vistaInversa"], 1, GL_TRUE, inversa)
        glUniform1i(_uniformes["modo"], MODO_NORMAL)
        _modo_actual = MODO_NORMAL
        _activo = True


def desactivar_shader():
    global _activo
    if _shader:
        glUseProgram(0)
    _activo = False
    glDisable(GL_FOG)


def set_modo(modo):
    # cambia el modo del shader
    global _modo_actual
    if _activo and modo != _modo_actual:
        glUniform1i(_uniformes["modo"], int(modo))
        _modo_actual = modo


# inicializacion
def init_lighting(usar_shader=True):
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_NORMALIZE)

    glEnable(GL_LIGHTING)
    for luz in (GL_LIGHT0, GL_LIGHT1, GL_LIGHT2):
        glEnable(luz)
        glLightfv(luz, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
        glLightf(luz, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(luz, GL_LINEAR_ATTENUATION, 0.0)
        glLightf(luz, GL_QUADRATIC_ATTENUATION, 0.0)

    # luz en las dos caras
    glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
    glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE)
    glLightModeli(GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR)

    # el color de cada material es ambiente y difuso
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])

    # niebla
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, NIEBLA_INICIO)
    glFogf(GL_FOG_END, NIEBLA_FIN)
    glHint(GL_FOG_HINT, GL_NICEST)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    if usar_shader:
        _crear_shader()
    update_light(estado['hora'])


# cada frame
def _calcular(hora):
    # angulo del sol: 0 a las 6, pi a las 18
    ang = (hora - 6.0) / 12.0 * math.pi
    dir_sol = _normalizar([math.cos(ang), math.sin(ang), 0.35])
    altura = dir_sol[1]

    factor_dia = _suavizar(-0.12, 0.18, altura)          # atardecer / amanecer
    dorado = 1.0 - _suavizar(0.02, 0.50, altura)          # luz mas calida cerca del horizonte

    color_sol = _mezclar(SOL_MEDIODIA, SOL_HORIZONTE, dorado)
    intensidad_sol = INTENSIDAD_SOL * _suavizar(-0.04, 0.30, altura)

    ambiente = _mezclar(AMBIENTE_NOCHE, _mezclar(AMBIENTE_DIA, AMBIENTE_ATARDECER, dorado), factor_dia)
    niebla = _mezclar(NIEBLA_NOCHE, _mezclar(NIEBLA_DIA, NIEBLA_ATARDECER, dorado), factor_dia)
    tinte = _mezclar(TINTE_CIELO_NOCHE, _mezclar(TINTE_CIELO_DIA, TINTE_CIELO_ATARDECER, dorado), factor_dia)

    dir_luna = _normalizar([-dir_sol[0], -dir_sol[1], 0.35])
    intensidad_luna = INTENSIDAD_LUNA * (1.0 - factor_dia) * _suavizar(-0.05, 0.25, dir_luna[1])

    # luz de relleno del lado contrario
    principal = dir_sol if factor_dia >= 0.5 else dir_luna
    dir_relleno = _normalizar([-principal[0], 0.6, -principal[2]])
    color_relleno = [c * 0.30 for c in ambiente]

    estado.update({
        'hora': hora,
        'factor_dia': factor_dia,
        'dir_sol': dir_sol,
        'dir_luna': dir_luna,
        'color_sol': color_sol,
        'tinte_cielo': tinte,
        'niebla': niebla,
    })
    return {
        'sol': ([c * intensidad_sol for c in color_sol], dir_sol),
        'luna': ([c * intensidad_luna for c in COLOR_LUNA], dir_luna),
        'relleno': (color_relleno, dir_relleno),
        'ambiente': ambiente,
        'niebla': niebla,
        'especular_sol': [c * intensidad_sol * 0.8 for c in color_sol],
        'especular_luna': [c * intensidad_luna * 0.5 for c in COLOR_LUNA],
    }


def update_light(hora=None):
    # actualiza las luces, va despues de gluLookAt
    if hora is None:
        hora = estado['hora']
    c = _calcular(hora)

    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, c['ambiente'] + [1.0])

    color, d = c['sol']
    glLightfv(GL_LIGHT0, GL_POSITION, d + [0.0])          # w = 0 es luz direccional
    glLightfv(GL_LIGHT0, GL_DIFFUSE, color + [1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, c['especular_sol'] + [1.0])

    color, d = c['luna']
    glLightfv(GL_LIGHT1, GL_POSITION, d + [0.0])
    glLightfv(GL_LIGHT1, GL_DIFFUSE, color + [1.0])
    glLightfv(GL_LIGHT1, GL_SPECULAR, c['especular_luna'] + [1.0])

    color, d = c['relleno']
    glLightfv(GL_LIGHT2, GL_POSITION, d + [0.0])
    glLightfv(GL_LIGHT2, GL_DIFFUSE, color + [1.0])
    glLightfv(GL_LIGHT2, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])

    glFogfv(GL_FOG_COLOR, c['niebla'] + [1.0])
    glClearColor(c['niebla'][0], c['niebla'][1], c['niebla'][2], 1.0)


# sol y luna
def _disco(centro, normal, radio, color_centro, color_borde, segmentos=32):
    # ejes perpendiculares a la direccion
    aux = [0.0, 1.0, 0.0] if abs(normal[1]) < 0.9 else [1.0, 0.0, 0.0]
    u = _normalizar([normal[1] * aux[2] - normal[2] * aux[1],
                     normal[2] * aux[0] - normal[0] * aux[2],
                     normal[0] * aux[1] - normal[1] * aux[0]])
    v = [normal[1] * u[2] - normal[2] * u[1],
         normal[2] * u[0] - normal[0] * u[2],
         normal[0] * u[1] - normal[1] * u[0]]
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(*color_centro)
    glVertex3f(*centro)
    glColor4f(*color_borde)
    for i in range(segmentos + 1):
        a = 2.0 * math.pi * i / segmentos
        ca, sa = math.cos(a) * radio, math.sin(a) * radio
        glVertex3f(centro[0] + u[0] * ca + v[0] * sa,
                   centro[1] + u[1] * ca + v[1] * sa,
                   centro[2] + u[2] * ca + v[2] * sa)
    glEnd()


def draw_light_source(cam_pos=(0.0, 0.0, 0.0)):
    # dibuja el sol o la luna, va justo despues del skybox
    glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_FOG)
    glDisable(GL_DEPTH_TEST)
    glDepthMask(GL_FALSE)
    glEnable(GL_BLEND)

    fd = estado['factor_dia']
    sol = estado['dir_sol']
    if sol[1] > -0.15:
        centro = [cam_pos[i] + sol[i] * DISTANCIA_ASTROS for i in range(3)]
        cs = estado['color_sol']
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)   # aditivo para el brillo
        _disco(centro, sol, 55.0, (cs[0], cs[1] * 0.95, cs[2] * 0.8, 0.30 * fd), (cs[0], cs[1], cs[2], 0.0))
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        _disco(centro, sol, 9.0, (1.0, 1.0, 0.95, 1.0), (cs[0], cs[1], cs[2], 0.9))

    luna = estado['dir_luna']
    if fd < 0.9 and luna[1] > -0.1:
        centro = [cam_pos[i] + luna[i] * DISTANCIA_ASTROS for i in range(3)]
        alfa = 1.0 - fd
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        _disco(centro, luna, 30.0, (0.55, 0.65, 0.9, 0.18 * alfa), (0.5, 0.6, 0.9, 0.0))
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        _disco(centro, luna, 6.0, (0.95, 0.96, 1.0, alfa), (0.80, 0.85, 0.95, alfa))

    glDepthMask(GL_TRUE)
    glPopAttrib()
