"""
Generador del PDF de la cédula de identidad.

El anverso reproduce la maquetación de la cédula venezolana: banda tricolor con
el encabezado, número de cédula y número de oficina, rúbrica del director,
apellidos y nombres, firma y huella del titular a la izquierda, los cuatro campos
de fechas/estado civil al centro, la nacionalidad y la fotografía a la derecha.

POSICIONES. Todas se expresan como FRACCIONES del ancho y del alto de la tarjeta
—medidas sobre la imagen de referencia de 1080x764 px—, no en centímetros
absolutos. Así el diseño se conserva al cambiar el tamaño de la tarjeta: basta
tocar `ANCHO_TARJETA`. Las fracciones verticales se cuentan DESDE ARRIBA, igual
que se leen en la imagen; `_fy()` las traduce al sistema de ReportLab, que mide
desde el borde inferior.

La huella que se estampa es la del dedo que el ciudadano eligió en el selector de
/renovacion (ver DEDOS en app/routes.py). Si no eligió ninguno, se usa la huella
principal del ciudadano (`Usuario.huella_ruta`).
"""
import os
import base64
import logging
from collections import namedtuple
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from app.utils.qr_generator import generar_qr, sumar_anios

logger = logging.getLogger(__name__)

# --- Tamaño de la tarjeta --------------------------------------------------
# Proporción tomada de la imagen de referencia (1080x764 px). La tarjeta queda
# algo más alta que una ID-1 real (85,6 x 54 mm) porque se respetó la proporción
# de la referencia para que la maquetación no salga estirada. Para volver a la
# proporción real basta poner PROPORCION_TARJETA = 85.6 / 54.
PROPORCION_TARJETA = 1080 / 764
ANCHO_TARJETA = 8.6 * cm
ALTO_TARJETA = ANCHO_TARJETA / PROPORCION_TARJETA
# Grosores de línea, como fracción del alto, para que la vista previa use los
# mismos que el PDF (donde están en puntos sobre ALTO_TARJETA).
GROSOR_BORDE = 0.8 / 172.5
GROSOR_RUBRICA = 0.7 / 172.5

# Posición de las dos caras en la hoja tamaño carta
X_ANVERSO = 2 * cm
SEPARACION_CARAS = 1 * cm
X_REVERSO = X_ANVERSO + ANCHO_TARJETA + SEPARACION_CARAS
Y_TARJETA = 20 * cm

# --- Colores --------------------------------------------------------------
# Los de la bandera, iguales a los que usa init_db.generar_bandera(). En la foto
# de referencia se ven lavados porque es un carnet gastado y fotografiado.
AMARILLO_BANDERA = (0.988, 0.819, 0.086)
AZUL_BANDERA = (0.0, 0.239, 0.647)
ROJO_BANDERA = (0.808, 0.067, 0.149)
GRIS_BORDE = (0.55, 0.55, 0.55)
GRIS_SUBTITULO = (0.35, 0.35, 0.35)
NEGRO = (0, 0, 0)
BLANCO = (1, 1, 1)

# --- Vista previa ---------------------------------------------------------
# La vista previa de /exito se dibuja como un SVG cuyo viewBox mide VB_ANCHO x
# VB_ALTO. Al usar las MISMAS fracciones que el PDF, cada elemento cae en el
# mismo sitio en las dos salidas. En SVG la `y` crece hacia abajo, igual que en
# las medidas de la referencia, así que no hace falta voltear nada.
VB_ANCHO = 1000.0
VB_ALTO = VB_ANCHO / PROPORCION_TARJETA

# --- Fracciones del anverso (medidas sobre la imagen de referencia) --------
# x: 0 = borde izquierdo, 1 = borde derecho
# y: 0 = borde SUPERIOR, 1 = borde inferior
ENC_X0, ENC_X1 = 0.075, 0.925
ENC_ALTO = 0.175
BANDA_AMARILLA = (0.005, 0.041)
BANDA_AZUL = (0.043, 0.079)
BANDA_ROJA = (0.082, 0.119)
ENC_TITULO_Y, ENC_TITULO_ANCHO = 0.074, 0.724
ENC_SUBTITULO_Y, ENC_SUBTITULO_ANCHO = 0.168, 0.680

CEDULA_CX, CEDULA_Y = 0.464, 0.241
SERIAL_CX, SERIAL_Y = 0.902, 0.240

DIR_FIRMA = (0.593, 0.190, 0.206, 0.128)      # x, y_superior, ancho, alto
DIR_NOMBRE_CX, DIR_NOMBRE_Y = 0.883, 0.314
DIR_CARGO_CX, DIR_CARGO_Y = 0.892, 0.335

ETIQUETA_X, VALOR_X = 0.008, 0.142
APELLIDOS_Y, NOMBRES_Y = 0.312, 0.381

FIRMA_CAJA = (0.028, 0.420, 0.148, 0.130)     # x, y_superior, ancho, alto
FIRMA_ETIQUETA = (0.005, 0.578)
HUELLA_CAJA = (0.018, 0.584, 0.178, 0.385)

CAMPO_COL1_X, CAMPO_COL2_X = 0.227, 0.419
CAMPO_ETIQUETA_SANGRIA = 0.021                # la etiqueta va indentada bajo su valor
CAMPO_FILA1_VALOR_Y, CAMPO_FILA1_ETIQUETA_Y = 0.668, 0.703
CAMPO_FILA2_VALOR_Y, CAMPO_FILA2_ETIQUETA_Y = 0.818, 0.852
NACIONALIDAD = (0.223, 0.946)

FOTO_CAJA = (0.648, 0.406, 0.324, 0.570)      # x, y_superior, ancho, alto

# Cuerpos de letra como fracción del alto de la tarjeta, deducidos de la altura
# de mayúscula medida en la referencia (Helvetica: mayúscula = 0,717 del cuerpo).
CUERPO_TITULO = 0.036
CUERPO_SUBTITULO = 0.040
CUERPO_CEDULA = 0.050
CUERPO_SERIAL = 0.057
CUERPO_DIR_NOMBRE = 0.036
CUERPO_DIR_CARGO = 0.026
CUERPO_ETIQUETA = 0.036
CUERPO_VALOR = 0.053
CUERPO_CAMPO = 0.085
CUERPO_CAMPO_ETIQUETA = 0.032
CUERPO_NACIONALIDAD = 0.075
CUERPO_FIRMA_ETIQUETA = 0.031

# Ancho que ocupa cada texto en la referencia, como fracción del ancho de la
# tarjeta. Si el texto no cabe se comprime en horizontal (ver _texto_condensado).
ANCHO_CEDULA = 0.215
ANCHO_SERIAL = 0.062
ANCHO_VALOR = 0.310
ANCHO_ETIQUETA = 0.131
ANCHO_CAMPO_COL1 = 0.180
ANCHO_CAMPO_COL2 = 0.195
ANCHO_CAMPO_ETIQUETA_COL1 = 0.130
ANCHO_CAMPO_ETIQUETA_COL2 = 0.140
ANCHO_NACIONALIDAD = 0.350
ANCHO_DIR_NOMBRE = 0.200
ANCHO_DIR_CARGO = 0.100
ANCHO_FIRMA_ETIQUETA = 0.124

# Nombre y cargo que van arriba a la derecha. Es un dato de maqueta: NO se usa el
# nombre de ningún funcionario real, y la rúbrica es un trazo genérico.
DIRECTOR_NOMBRE = 'Dr. J. Pérez Marín'
DIRECTOR_CARGO = 'Director'

# Trazo de la rúbrica, en fracciones de su propia caja. Está aquí, y no dentro de
# la función que la dibuja, porque lo comparten el PDF y la vista previa.
RUBRICA_INICIO = (0.02, 0.32)
RUBRICA_CURVAS = (
    (0.10, 0.95, 0.20, 0.08, 0.32, 0.56),
    (0.42, 0.94, 0.50, 0.04, 0.62, 0.46),
    (0.74, 0.88, 0.86, 0.10, 0.99, 0.54),
)
RUBRICA_LAZO_INICIO = (0.05, 0.36)
RUBRICA_LAZO = (-0.02, 0.80, 0.16, 0.86, 0.13, 0.42)
RUBRICA_RASGO = (0.00, 0.26, 1.00, 0.34)

# --- Reverso --------------------------------------------------------------
REV_BARRA_ALTO = 0.13
REV_QR_LADO = 0.46          # fracción del alto de la tarjeta
REV_QR_Y = 0.22             # borde superior del QR
# (texto, cx, línea base, cuerpo, fuente, color)
TEXTOS_REVERSO = (
    ('SAIME', 0.5, 0.095, 0.060, 'Helvetica-Bold', BLANCO),
    ('Escanee para verificar', 0.5, 0.760, 0.040, 'Helvetica', NEGRO),
    ('Servicio Administrativo de Identificación,', 0.5, 0.840, 0.034, 'Helvetica', NEGRO),
    ('Migración y Extranjería', 0.5, 0.895, 0.034, 'Helvetica', NEGRO),
    ('Documento válido en todo el territorio nacional', 0.5, 0.960, 0.028, 'Helvetica', NEGRO),
)

# Un texto del anverso: qué dice, dónde va y cómo se ajusta.
#   alineacion: 'izq' | 'centro'   (x es el borde izquierdo o el centro)
#   modo:       'condensar' comprime si no cabe en `ancho`
#               'expandir'  separa las letras hasta ocupar `ancho`
TextoAnverso = namedtuple(
    'TextoAnverso',
    'clave texto x y cuerpo ancho alineacion modo color',
    defaults=('izq', 'condensar', NEGRO),
)


# --- Ayudas de coordenadas ------------------------------------------------
def _fx(caja, fraccion):
    """Fracción horizontal (0 = izquierda, 1 = derecha) -> coordenada absoluta."""
    return caja[0] + caja[2] * fraccion


def _fy(caja, fraccion):
    """
    Fracción vertical contada DESDE ARRIBA -> coordenada absoluta.

    Las medidas se tomaron sobre la imagen de referencia, donde y crece hacia
    abajo, mientras ReportLab mide desde el borde inferior de la página.
    """
    return caja[1] + caja[3] * (1.0 - fraccion)


def _cuerpo(fraccion):
    """Cuerpo de letra en puntos a partir de su fracción del alto de la tarjeta."""
    return fraccion * ALTO_TARJETA


def _ancho_con_espaciado(c, texto, espaciado):
    return c.stringWidth(texto, c._fontname, c._fontsize) + espaciado * max(0, len(texto) - 1)


def _espaciado_para_ancho(c, texto, ancho_objetivo):
    """
    Separación entre letras necesaria para que `texto` ocupe `ancho_objetivo`.

    El encabezado de la cédula lleva las letras muy separadas. Calcular el
    espaciado a partir del ancho deseado (en vez de fijarlo a ojo) garantiza que
    el texto abarque lo mismo que en la referencia con cualquier cuerpo de letra.
    """
    base = c.stringWidth(texto, c._fontname, c._fontsize)
    return max(0.0, (ancho_objetivo - base) / max(1, len(texto) - 1))


def _texto_condensado(c, x, y, texto, ancho_max, centrado=False):
    """
    Dibuja texto comprimiéndolo en horizontal si no cabe en `ancho_max`.

    La cédula real está impresa con una tipografía CONDENSADA. Con Helvetica,
    respetar la altura de mayúscula medida en la referencia deja el texto
    demasiado ancho, y bajar el cuerpo para que quepa lo dejaría mucho más bajo
    que en el original. La salida es comprimir en horizontal con `Tz`, que es
    exactamente lo que hace una condensada: se conservan a la vez la altura y el
    ancho que tiene cada dato en la referencia.

    Sirve además para los datos reales, que no miden lo mismo que los de la
    imagen ('RODRÍGUEZ PÉREZ' es más largo que 'ARONICO TORRES'): sin esto se
    montaban sobre la columna siguiente.
    """
    if not texto:
        return
    ancho = c.stringWidth(texto, c._fontname, c._fontsize)
    escala = 100.0 * ancho_max / ancho if ancho > ancho_max else 100.0
    ancho_final = ancho * escala / 100.0
    c.saveState()
    objeto = c.beginText(x - (ancho_final / 2.0 if centrado else 0.0), y)
    # Igual que charSpace, la escala horizontal persiste en el estado gráfico:
    # de ahí el saveState/restoreState que envuelve el bloque.
    objeto.setHorizScale(escala)
    objeto.textOut(texto)
    c.drawText(objeto)
    c.restoreState()


def _texto_espaciado(c, x, y, texto, espaciado):
    """
    Dibuja texto con separación extra entre letras. ReportLab expone charSpace en
    el OBJETO DE TEXTO, no en el canvas (`canvas.setCharSpace` no existe), así
    que se pasa por beginText/drawText, que heredan fuente y color del canvas.

    El saveState/restoreState es imprescindible: el charSpace (operador `Tc`)
    forma parte del ESTADO GRÁFICO del PDF y PERSISTE al cerrar el bloque de
    texto. Sin aislarlo, la separación del encabezado se filtraba a todos los
    textos siguientes y la tarjeta salía con las letras desparramadas.
    """
    c.saveState()
    objeto = c.beginText(x, y)
    objeto.setCharSpace(espaciado)
    objeto.textOut(texto)
    c.drawText(objeto)
    c.restoreState()


def _centrado_espaciado(c, cx, y, texto, espaciado):
    """Texto centrado teniendo en cuenta la separación extra entre letras."""
    _texto_espaciado(c, cx - _ancho_con_espaciado(c, texto, espaciado) / 2.0, y, texto, espaciado)


def _dibujar_imagen(c, ruta, x, y, ancho, alto, etiqueta):
    """
    Dibuja una imagen ajustada a la caja SIN deformarla.

    Si el archivo falta o falla, deja el recuadro vacío en su lugar en vez de
    tumbar el PDF: un ciudadano de prueba puede no tener firma ni huella.
    """
    if not ruta or not os.path.exists(ruta):
        logger.warning(f"No se encontró la imagen de {etiqueta}: {ruta}")
        c.rect(x, y, ancho, alto, stroke=1, fill=0)
        return False
    try:
        c.drawImage(ruta, x, y, width=ancho, height=alto,
                    preserveAspectRatio=True, anchor='c', mask='auto')
        return True
    except Exception as e:
        logger.warning(f"No se pudo dibujar la imagen de {etiqueta}: {e}")
        c.rect(x, y, ancho, alto, stroke=1, fill=0)
        return False


# --- Formateo de datos ----------------------------------------------------
def _partes_cedula(cedula):
    """
    'V-12345678' -> ('V', '12.345.678'), como se imprime en la cédula real.
    """
    texto = (cedula or '').strip().upper()
    letra, _, numero = texto.partition('-')
    if not numero:
        letra, numero = 'V', texto
    digitos = ''.join(ch for ch in numero if ch.isdigit())
    grupos = []
    while len(digitos) > 3:
        grupos.insert(0, digitos[-3:])
        digitos = digitos[:-3]
    if digitos:
        grupos.insert(0, digitos)
    return (letra or 'V'), '.'.join(grupos)


def _serial_oficina(cedula):
    """
    Número de oficina que la cédula lleva arriba a la derecha (en la referencia,
    '113'). Se deriva de la cédula para que sea estable entre generaciones del
    mismo ciudadano. Es un dato de maqueta, no un código real.
    """
    digitos = ''.join(ch for ch in (cedula or '') if ch.isdigit())
    return f"{((int(digitos) % 900) + 100) if digitos else 100:03d}"


def _nacionalidad(cedula):
    return 'EXTRANJERO' if (cedula or '').strip().upper().startswith('E-') else 'VENEZOLANO'


def datos_qr(usuario):
    """Datos que codifica el QR del reverso. Compartidos con la vista previa."""
    return {
        'nombres': usuario.nombres,
        'apellidos': usuario.apellidos,
        'cedula': usuario.cedula,
        'fecha_nacimiento': _fecha(usuario.fecha_nacimiento),
    }


def _fecha(valor, formato='%d/%m/%Y'):
    return valor.strftime(formato) if hasattr(valor, 'strftime') else str(valor or '')


def _ruta_estatica(relativa):
    """Convierte una ruta relativa del modelo (p. ej. 'huellas/V-1.png') en absoluta."""
    if not relativa:
        return None
    if os.path.isabs(relativa):
        return relativa
    from flask import current_app
    return os.path.join(current_app.static_folder, relativa)


def datos_anverso(usuario):
    """
    Los textos del anverso ya formateados.

    Los usan el PDF y la vista previa de /exito, así que ninguno de los dos puede
    mostrar un dato distinto del otro (fechas incluidas: la de expedición es la
    de hoy y la de vencimiento se calcula igual en ambos).
    """
    hoy = datetime.now()
    letra, numero = _partes_cedula(usuario.cedula)
    return {
        'cedula': f"{letra}   {numero}",
        'serial': _serial_oficina(usuario.cedula),
        'apellidos': (usuario.apellidos or '').upper(),
        'nombres': (usuario.nombres or '').upper(),
        'nacimiento': _fecha(usuario.fecha_nacimiento),
        'estado_civil': (usuario.estado_civil or '').upper(),
        'expedicion': hoy.strftime('%d/%m/%Y'),
        # En la cédula real el vencimiento se imprime solo como mes/año
        'vencimiento': sumar_anios(hoy, 10).strftime('%m/%Y'),
        'nacionalidad': _nacionalidad(usuario.cedula),
        'director_nombre': DIRECTOR_NOMBRE,
        'director_cargo': DIRECTOR_CARGO,
    }


def _especificacion_anverso(datos):
    """
    Todos los textos del anverso en un solo sitio: qué dicen, dónde van (en
    fracciones), con qué cuerpo, cuánto deben ocupar y cómo se alinean.

    Es la ÚNICA definición de la maquetación de textos. La recorre el PDF para
    dibujar y la recorre `vista_previa()` para armar el SVG de /exito, de modo
    que la vista previa no puede desviarse del documento que se descarga: mover o
    agregar un campo aquí lo mueve o lo agrega en los dos.
    """
    centro_encabezado = (ENC_X0 + ENC_X1) / 2.0
    return [
        TextoAnverso('titulo', 'REPUBLICA BOLIVARIANA DE VENEZUELA',
                     centro_encabezado, ENC_TITULO_Y, CUERPO_TITULO,
                     ENC_TITULO_ANCHO, 'centro', 'expandir', BLANCO),
        TextoAnverso('subtitulo', 'CEDULA DE IDENTIDAD',
                     centro_encabezado, ENC_SUBTITULO_Y, CUERPO_SUBTITULO,
                     ENC_SUBTITULO_ANCHO, 'centro', 'expandir', GRIS_SUBTITULO),
        TextoAnverso('cedula', datos['cedula'], CEDULA_CX, CEDULA_Y,
                     CUERPO_CEDULA, ANCHO_CEDULA, 'centro'),
        TextoAnverso('serial', datos['serial'], SERIAL_CX, SERIAL_Y,
                     CUERPO_SERIAL, ANCHO_SERIAL, 'centro'),
        TextoAnverso('director_nombre', datos['director_nombre'],
                     DIR_NOMBRE_CX, DIR_NOMBRE_Y, CUERPO_DIR_NOMBRE,
                     ANCHO_DIR_NOMBRE, 'centro'),
        TextoAnverso('director_cargo', datos['director_cargo'],
                     DIR_CARGO_CX, DIR_CARGO_Y, CUERPO_DIR_CARGO,
                     ANCHO_DIR_CARGO, 'centro'),
        TextoAnverso('apellidos_etiqueta', 'APELLIDOS', ETIQUETA_X, APELLIDOS_Y,
                     CUERPO_ETIQUETA, ANCHO_ETIQUETA),
        TextoAnverso('apellidos', datos['apellidos'], VALOR_X, APELLIDOS_Y,
                     CUERPO_VALOR, ANCHO_VALOR),
        TextoAnverso('nombres_etiqueta', 'NOMBRES', ETIQUETA_X, NOMBRES_Y,
                     CUERPO_ETIQUETA, ANCHO_ETIQUETA),
        TextoAnverso('nombres', datos['nombres'], VALOR_X, NOMBRES_Y,
                     CUERPO_VALOR, ANCHO_VALOR),
        TextoAnverso('firma_etiqueta', 'FIRMA TITULAR', FIRMA_ETIQUETA[0],
                     FIRMA_ETIQUETA[1], CUERPO_FIRMA_ETIQUETA, ANCHO_FIRMA_ETIQUETA),
        TextoAnverso('nacimiento', datos['nacimiento'], CAMPO_COL1_X,
                     CAMPO_FILA1_VALOR_Y, CUERPO_CAMPO, ANCHO_CAMPO_COL1),
        TextoAnverso('nacimiento_etiqueta', 'F. NACIMIENTO',
                     CAMPO_COL1_X + CAMPO_ETIQUETA_SANGRIA, CAMPO_FILA1_ETIQUETA_Y,
                     CUERPO_CAMPO_ETIQUETA, ANCHO_CAMPO_ETIQUETA_COL1),
        TextoAnverso('estado_civil', datos['estado_civil'], CAMPO_COL2_X,
                     CAMPO_FILA1_VALOR_Y, CUERPO_CAMPO, ANCHO_CAMPO_COL2),
        TextoAnverso('estado_civil_etiqueta', 'EDO.CIVIL',
                     CAMPO_COL2_X + CAMPO_ETIQUETA_SANGRIA, CAMPO_FILA1_ETIQUETA_Y,
                     CUERPO_CAMPO_ETIQUETA, ANCHO_CAMPO_ETIQUETA_COL2),
        TextoAnverso('expedicion', datos['expedicion'], CAMPO_COL1_X,
                     CAMPO_FILA2_VALOR_Y, CUERPO_CAMPO, ANCHO_CAMPO_COL1),
        TextoAnverso('expedicion_etiqueta', 'F.EXPEDICION',
                     CAMPO_COL1_X + CAMPO_ETIQUETA_SANGRIA, CAMPO_FILA2_ETIQUETA_Y,
                     CUERPO_CAMPO_ETIQUETA, ANCHO_CAMPO_ETIQUETA_COL1),
        TextoAnverso('vencimiento', datos['vencimiento'], CAMPO_COL2_X,
                     CAMPO_FILA2_VALOR_Y, CUERPO_CAMPO, ANCHO_CAMPO_COL2),
        TextoAnverso('vencimiento_etiqueta', 'F.VENCIMIENTO',
                     CAMPO_COL2_X + CAMPO_ETIQUETA_SANGRIA, CAMPO_FILA2_ETIQUETA_Y,
                     CUERPO_CAMPO_ETIQUETA, ANCHO_CAMPO_ETIQUETA_COL2),
        TextoAnverso('nacionalidad', datos['nacionalidad'], NACIONALIDAD[0],
                     NACIONALIDAD[1], CUERPO_NACIONALIDAD, ANCHO_NACIONALIDAD),
    ]


# --- Rúbrica del director -------------------------------------------------
def _rubrica_director(c, x, y, ancho, alto):
    """
    Trazo decorativo en el lugar donde la cédula real lleva la firma del
    director. Es un garabato genérico dibujado con líneas: no reproduce la firma
    de ninguna persona.
    """
    def px(f):
        return x + f * ancho

    def py(f):
        return y + f * alto

    c.saveState()
    c.setLineWidth(GROSOR_RUBRICA * ALTO_TARJETA)
    c.setStrokeColorRGB(0.10, 0.10, 0.20)

    # Trazo principal, con curvas para que parezca escrito a mano y no un zigzag
    camino = c.beginPath()
    camino.moveTo(px(RUBRICA_INICIO[0]), py(RUBRICA_INICIO[1]))
    for x1, y1, x2, y2, x3, y3 in RUBRICA_CURVAS:
        camino.curveTo(px(x1), py(y1), px(x2), py(y2), px(x3), py(y3))
    c.drawPath(camino)

    # Lazo inicial y rasgo largo que cruza la rúbrica, como en el original
    lazo = c.beginPath()
    lazo.moveTo(px(RUBRICA_LAZO_INICIO[0]), py(RUBRICA_LAZO_INICIO[1]))
    lazo.curveTo(px(RUBRICA_LAZO[0]), py(RUBRICA_LAZO[1]), px(RUBRICA_LAZO[2]),
                 py(RUBRICA_LAZO[3]), px(RUBRICA_LAZO[4]), py(RUBRICA_LAZO[5]))
    c.drawPath(lazo)
    c.line(px(RUBRICA_RASGO[0]), py(RUBRICA_RASGO[1]),
           px(RUBRICA_RASGO[2]), py(RUBRICA_RASGO[3]))
    c.restoreState()


# --- Anverso --------------------------------------------------------------
def _dibujar_anverso(c, usuario, ruta_foto, ruta_huella):
    caja = (X_ANVERSO, Y_TARJETA, ANCHO_TARJETA, ALTO_TARJETA)

    # Fondo y borde de la tarjeta
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(*GRIS_BORDE)
    c.setLineWidth(0.8)
    c.rect(caja[0], caja[1], caja[2], caja[3], stroke=1, fill=1)

    # --- Encabezado: bandas tricolor recortadas por un rectángulo redondeado,
    # para que los extremos de las bandas queden curvos como en el original.
    hx0, hx1 = _fx(caja, ENC_X0), _fx(caja, ENC_X1)
    h_sup, h_inf = _fy(caja, 0.0), _fy(caja, ENC_ALTO)
    radio = (hx1 - hx0) * 0.035

    c.saveState()
    recorte = c.beginPath()
    recorte.roundRect(hx0, h_inf, hx1 - hx0, h_sup - h_inf, radio)
    c.clipPath(recorte, stroke=0, fill=0)
    for (f_sup, f_inf), color in ((BANDA_AMARILLA, AMARILLO_BANDERA),
                                  (BANDA_AZUL, AZUL_BANDERA),
                                  (BANDA_ROJA, ROJO_BANDERA)):
        c.setFillColorRGB(*color)
        c.rect(hx0, _fy(caja, f_inf), hx1 - hx0,
               (f_inf - f_sup) * ALTO_TARJETA, stroke=0, fill=1)
    c.restoreState()

    c.setStrokeColorRGB(*GRIS_BORDE)
    c.roundRect(hx0, h_inf, hx1 - hx0, h_sup - h_inf, radio, stroke=1, fill=0)

    # --- Rúbrica del director (debajo de los textos)
    dx, dy_sup, dw, dh = DIR_FIRMA
    _rubrica_director(c, _fx(caja, dx), _fy(caja, dy_sup + dh),
                      dw * ANCHO_TARJETA, dh * ALTO_TARJETA)

    # --- Imágenes: firma y huella del titular a la izquierda, foto a la derecha
    for ruta, (ix, iy_sup, iw, ih), etiqueta in (
            (_ruta_estatica(usuario.firma_ruta), FIRMA_CAJA, 'firma'),
            (ruta_huella, HUELLA_CAJA, 'huella'),
            (ruta_foto, FOTO_CAJA, 'fotografía')):
        _dibujar_imagen(c, ruta, _fx(caja, ix), _fy(caja, iy_sup + ih),
                        iw * ANCHO_TARJETA, ih * ALTO_TARJETA, etiqueta)

    # --- Textos: se recorre la especificación compartida con la vista previa
    for t in _especificacion_anverso(datos_anverso(usuario)):
        if not t.texto:
            continue
        c.setFillColorRGB(*t.color)
        c.setFont('Helvetica-Bold', _cuerpo(t.cuerpo))
        x, y = _fx(caja, t.x), _fy(caja, t.y)
        objetivo = t.ancho * ANCHO_TARJETA
        if t.modo == 'expandir':
            espaciado = _espaciado_para_ancho(c, t.texto, objetivo)
            if t.alineacion == 'centro':
                _centrado_espaciado(c, x, y, t.texto, espaciado)
            else:
                _texto_espaciado(c, x, y, t.texto, espaciado)
        else:
            _texto_condensado(c, x, y, t.texto, objetivo,
                              centrado=(t.alineacion == 'centro'))


# --- Reverso --------------------------------------------------------------
def _dibujar_reverso(c, usuario, ruta_salida):
    caja = (X_REVERSO, Y_TARJETA, ANCHO_TARJETA, ALTO_TARJETA)

    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(*GRIS_BORDE)
    c.setLineWidth(GROSOR_BORDE * ALTO_TARJETA)
    c.rect(caja[0], caja[1], caja[2], caja[3], stroke=1, fill=1)

    # Barra superior azul con el nombre del organismo
    c.setFillColorRGB(*AZUL_BANDERA)
    c.rect(caja[0], _fy(caja, REV_BARRA_ALTO), caja[2],
           REV_BARRA_ALTO * ALTO_TARJETA, stroke=0, fill=1)

    # Código QR con los datos del ciudadano
    lado = REV_QR_LADO * ALTO_TARJETA
    qr_x = _fx(caja, 0.5) - lado / 2.0
    qr_y = _fy(caja, REV_QR_Y + REV_QR_LADO)
    try:
        ruta_qr = os.path.join(os.path.dirname(ruta_salida), f"qr_{usuario.cedula}.png")
        generar_qr(datos_qr(usuario), ruta_qr)
        c.drawImage(ruta_qr, qr_x, qr_y, width=lado, height=lado)
        if os.path.exists(ruta_qr):
            os.remove(ruta_qr)
    except Exception as e:
        logger.warning(f"Error al generar QR: {e}")
        c.setStrokeColorRGB(*GRIS_BORDE)
        c.rect(qr_x, qr_y, lado, lado, stroke=1, fill=0)

    # Textos: misma lista que recorre la vista previa
    for texto, cx, y, cuerpo, fuente, color in TEXTOS_REVERSO:
        c.setFillColorRGB(*color)
        c.setFont(fuente, _cuerpo(cuerpo))
        c.drawCentredString(_fx(caja, cx), _fy(caja, y), texto)


# --- Vista previa en SVG --------------------------------------------------
def _css(color):
    """Color RGB de ReportLab (0-1) a hexadecimal de CSS."""
    return '#%02x%02x%02x' % tuple(int(round(componente * 255)) for componente in color)


def _rubrica_svg():
    """
    La rúbrica como atributo `d` de un <path> de SVG, con el mismo trazo que
    dibuja el PDF pero en coordenadas del viewBox.
    """
    x0, y_sup, ancho, alto = DIR_FIRMA

    def px(f):
        return round((x0 + f * ancho) * VB_ANCHO, 2)

    def py(f):
        return round((y_sup + f * alto) * VB_ALTO, 2)

    partes = [f"M {px(RUBRICA_INICIO[0])} {py(RUBRICA_INICIO[1])}"]
    for x1, y1, x2, y2, x3, y3 in RUBRICA_CURVAS:
        partes.append(f"C {px(x1)} {py(y1)} {px(x2)} {py(y2)} {px(x3)} {py(y3)}")
    partes.append(f"M {px(RUBRICA_LAZO_INICIO[0])} {py(RUBRICA_LAZO_INICIO[1])}")
    partes.append(f"C {px(RUBRICA_LAZO[0])} {py(RUBRICA_LAZO[1])} "
                  f"{px(RUBRICA_LAZO[2])} {py(RUBRICA_LAZO[3])} "
                  f"{px(RUBRICA_LAZO[4])} {py(RUBRICA_LAZO[5])}")
    partes.append(f"M {px(RUBRICA_RASGO[0])} {py(RUBRICA_RASGO[1])} "
                  f"L {px(RUBRICA_RASGO[2])} {py(RUBRICA_RASGO[3])}")
    return ' '.join(partes)


def _texto_svg(texto, cx_o_x, y, cuerpo_fraccion, ancho_fraccion, alineacion, modo, color,
               fuente='Helvetica-Bold'):
    """
    Un texto listo para emitir como <text> de SVG, replicando cómo lo ajusta el PDF.

    La correspondencia es directa: `lengthAdjust="spacing"` reparte el hueco entre
    las letras, igual que el charSpace (`Tc`) del modo 'expandir'; y
    `lengthAdjust="spacingAndGlyphs"` estrecha los glifos, igual que la escala
    horizontal (`Tz`) del modo 'condensar'. El ancho natural se mide con las
    métricas de Helvetica de ReportLab —las mismas que usa el PDF—, así que se
    condensa exactamente en los mismos casos.
    """
    cuerpo = cuerpo_fraccion * VB_ALTO
    objetivo = ancho_fraccion * VB_ANCHO
    natural = pdfmetrics.stringWidth(texto, fuente, cuerpo)
    if modo == 'expandir':
        largo, ajuste = objetivo, 'spacing'
    elif natural > objetivo:
        largo, ajuste = objetivo, 'spacingAndGlyphs'
    else:
        largo, ajuste = None, None
    return {
        'texto': texto,
        'x': round(cx_o_x * VB_ANCHO, 2),
        'y': round(y * VB_ALTO, 2),
        'cuerpo': round(cuerpo, 2),
        'anclaje': 'middle' if alineacion == 'centro' else 'start',
        'largo': round(largo, 2) if largo else None,
        'ajuste': ajuste,
        'color': _css(color),
        'negrita': fuente.endswith('Bold'),
    }


def vista_previa(usuario):
    """
    Modelo de las dos caras de la cédula para la vista previa en SVG de /exito.

    Todo sale de las MISMAS constantes, los mismos datos formateados y el mismo
    criterio de ajuste de ancho que usa el PDF, en unidades del viewBox
    (VB_ANCHO x VB_ALTO). Es decir: la vista previa no es un dibujo aparte que
    haya que mantener en paralelo, sino la misma maquetación renderizada en SVG,
    así que no puede desviarse del documento que el ciudadano descarga.
    """
    datos = datos_anverso(usuario)

    bandas = [
        {'y': round(f_sup * VB_ALTO, 2),
         'alto': round((f_inf - f_sup) * VB_ALTO, 2),
         'color': _css(color)}
        for (f_sup, f_inf), color in ((BANDA_AMARILLA, AMARILLO_BANDERA),
                                      (BANDA_AZUL, AZUL_BANDERA),
                                      (BANDA_ROJA, ROJO_BANDERA))
    ]

    def recuadro(caja):
        x, y_sup, ancho, alto = caja
        return {'x': round(x * VB_ANCHO, 2), 'y': round(y_sup * VB_ALTO, 2),
                'ancho': round(ancho * VB_ANCHO, 2), 'alto': round(alto * VB_ALTO, 2)}

    # QR incrustado como data URI: se genera con la misma función y los mismos
    # datos que el QR del PDF, así que ambos codifican lo mismo.
    try:
        qr = ('data:image/png;base64,'
              + base64.b64encode(generar_qr(datos_qr(usuario)).getvalue()).decode('ascii'))
    except Exception as e:
        logger.warning(f"No se pudo generar el QR de la vista previa: {e}")
        qr = None

    lado_qr = REV_QR_LADO * VB_ALTO
    return {
        'ancho': round(VB_ANCHO, 2),
        'alto': round(VB_ALTO, 2),
        'borde': _css(GRIS_BORDE),
        'grosor_borde': round(GROSOR_BORDE * VB_ALTO, 2),
        'anverso': {
            'encabezado': {
                'x': round(ENC_X0 * VB_ANCHO, 2),
                'ancho': round((ENC_X1 - ENC_X0) * VB_ANCHO, 2),
                'alto': round(ENC_ALTO * VB_ALTO, 2),
                'radio': round((ENC_X1 - ENC_X0) * VB_ANCHO * 0.035, 2),
                'bandas': bandas,
            },
            'rubrica': {'d': _rubrica_svg(),
                        'grosor': round(GROSOR_RUBRICA * VB_ALTO, 2),
                        'color': _css((0.10, 0.10, 0.20))},
            'imagenes': {'firma': recuadro(FIRMA_CAJA), 'huella': recuadro(HUELLA_CAJA),
                         'foto': recuadro(FOTO_CAJA)},
            'textos': [_texto_svg(t.texto, t.x, t.y, t.cuerpo, t.ancho,
                                  t.alineacion, t.modo, t.color)
                       for t in _especificacion_anverso(datos) if t.texto],
        },
        'reverso': {
            'barra': {'alto': round(REV_BARRA_ALTO * VB_ALTO, 2),
                      'color': _css(AZUL_BANDERA)},
            'qr': {'src': qr,
                   'x': round(VB_ANCHO / 2 - lado_qr / 2, 2),
                   'y': round(REV_QR_Y * VB_ALTO, 2),
                   'lado': round(lado_qr, 2)},
            'textos': [_texto_svg(texto, cx, y, cuerpo, 1.0, 'centro', 'natural',
                                  color, fuente)
                       for texto, cx, y, cuerpo, fuente, color in TEXTOS_REVERSO],
        },
    }


# --- API ------------------------------------------------------------------
def generar_cedula_pdf(usuario, ruta_foto_nueva, ruta_salida, ruta_huella=None):
    """
    Genera el PDF con el anverso y el reverso de la cédula.

    Args:
        usuario: objeto Usuario con los datos del ciudadano.
        ruta_foto_nueva: ruta a la fotografía aprobada en el trámite.
        ruta_salida: ruta donde guardar el PDF.
        ruta_huella: ruta ABSOLUTA de la huella a estampar (la del dedo elegido
            en el selector de /renovacion). Si no se indica o el archivo no
            existe, se usa la huella principal del ciudadano.

    Returns:
        str: ruta al PDF generado, o None si falló.
    """
    try:
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

        if not ruta_huella or not os.path.exists(ruta_huella):
            if ruta_huella:
                logger.warning(f"La huella elegida no existe ({ruta_huella}); "
                               f"se usa la huella principal del ciudadano.")
            ruta_huella = _ruta_estatica(usuario.huella_ruta)

        c = canvas.Canvas(ruta_salida, pagesize=letter)
        _dibujar_anverso(c, usuario, ruta_foto_nueva, ruta_huella)
        _dibujar_reverso(c, usuario, ruta_salida)
        c.save()
        return ruta_salida
    except Exception as e:
        logger.error(f"Error generando PDF de cédula: {e}")
        return None


def generar_pdf(usuario, ruta_foto_nueva, ruta_huella=None):
    """
    Envoltorio compatible con routes.py: calcula la ruta de salida dentro del
    directorio de subidas.
    """
    from flask import current_app
    upload_folder = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'])
    ruta_salida = os.path.join(upload_folder, f"cedula_{usuario.cedula}.pdf")
    return generar_cedula_pdf(usuario, ruta_foto_nueva, ruta_salida, ruta_huella=ruta_huella)
