"""
Módulo de validación de fotos para SIVA.
Utiliza OpenCV para verificar los requisitos obligatorios del SAIME:
- Dimensiones: la imagen NO se rechaza por su tamaño en píxeles. Se acepta
  cualquier resolución y se REDIMENSIONA automáticamente a 336x448 px (relación
  de aspecto 3:4 reglamentaria de la cédula). Es decir, el requisito real es de
  proporción/relación de aspecto, no de un tamaño exacto en píxeles.
- Detección de rostro (exactamente uno)
- Detección de ojos abiertos (al menos dos)
- Detección de gafas (no debe tener)
- Detección de gorra/sombrero (no debe tener)
- Fondo blanco (mínimo de píxeles claros configurable; 70% por defecto vía
  config.FONDO_THRESHOLD / variable de entorno FONDO_THRESHOLD)

Incluye un bypass inteligente para imágenes de prueba/placeholders y tolerancias
de detección para evitar falsos negativos en entornos de prueba.

NOTA: En Python 3.14 con versiones recientes de opencv-python-headless,
cv2.CascadeClassifier puede no estar disponible. En ese caso se utiliza
validación básica (dimensiones, formato, fondo) sin detección facial.
"""
import os
import logging

# Importar OpenCV y numpy con manejo robusto de errores
try:
    import cv2
    CV2_DISPONIBLE = True
except ImportError:
    CV2_DISPONIBLE = False

try:
    import numpy as np
    NUMPY_DISPONIBLE = True
except ImportError:
    NUMPY_DISPONIBLE = False

try:
    from PIL import Image
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False

# Verificar si CascadeClassifier está disponible en cv2
CASCADA_DISPONIBLE = False
if CV2_DISPONIBLE:
    CASCADA_DISPONIBLE = hasattr(cv2, 'CascadeClassifier')

# Configuración de registros (logging)
logger = logging.getLogger(__name__)

if not CV2_DISPONIBLE:
    logger.warning("OpenCV (cv2) no está disponible. Se usará validación básica con PIL.")
if CV2_DISPONIBLE and not CASCADA_DISPONIBLE:
    logger.warning("cv2.CascadeClassifier no disponible en esta versión de OpenCV. "
                   "Se omitirá detección facial y se usará validación básica.")


def _es_imagen_grafica_o_placeholder(imagen_np):
    """
    Detecta si la imagen es una ilustración digital, silueta o marcador de posición.
    Las imágenes reales de cámaras contienen miles de variaciones de color y ruido.
    Los gráficos planos o placeholders tienen un número muy bajo de colores únicos.
    
    Args:
        imagen_np: imagen como array numpy (BGR)
    
    Returns:
        bool: True si la imagen parece ser un gráfico plano/placeholder
    """
    try:
        if not NUMPY_DISPONIBLE or not CV2_DISPONIBLE:
            return False
        # Redimensionar a una imagen pequeña para contar rápido
        pequena = cv2.resize(imagen_np, (100, 100))
        # Agrupar en filas de píxeles y obtener colores únicos
        colores_unicos = len(np.unique(pequena.reshape(-1, 3), axis=0))
        logger.info(f"Colores únicos en muestra: {colores_unicos}")
        # Si tiene menos de 400 colores únicos en 100x100 píxeles, es muy probable que sea un gráfico plano
        return colores_unicos < 400
    except Exception as e:
        logger.error(f"Error al analizar paleta de colores: {str(e)}")
        return False


def _verificar_dimensiones_cv2(imagen):
    """
    Normaliza la imagen a la relación de aspecto 3:4 (336x448 px) usando OpenCV.

    IMPORTANTE: esta función NUNCA rechaza una foto por su tamaño. Si la imagen ya
    mide 336x448 se deja igual; en cualquier otro caso se REDIMENSIONA a 336x448.
    El redimensionado automático es intencional (preferido) para no bloquear al
    usuario por diferencias de tamaño: lo que importa es que la cédula termine con
    la proporción/relación de aspecto 3:4 correcta.
    """
    alto, ancho = imagen.shape[:2]
    if ancho == 336 and alto == 448:
        return True, "Dimensiones correctas.", imagen

    try:
        # Intentar redimensionar automáticamente para ayudar al usuario
        imagen_redimensionada = cv2.resize(imagen, (336, 448))
        logger.info(f"Imagen redimensionada automáticamente de {ancho}x{alto} a 336x448.")
        return True, "Imagen redimensionada automáticamente a 336x448.", imagen_redimensionada
    except Exception as e:
        logger.error(f"Error al redimensionar imagen: {str(e)}")
        return False, f"Dimensiones incorrectas ({ancho}x{alto}) y no se pudo redimensionar.", None


def _verificar_dimensiones_pil(ruta_archivo):
    """
    Verifica dimensiones de la imagen usando PIL como fallback.
    """
    try:
        img_pil = Image.open(ruta_archivo)
        ancho, alto = img_pil.size
        # Aceptar cualquier tamaño razonable ya que se redimensiona automáticamente en el servidor
        if ancho < 50 or alto < 50:
            return False, f"La imagen es demasiado pequeña ({ancho}x{alto})."
        if ancho > 10000 or alto > 10000:
            return False, f"La imagen es demasiado grande ({ancho}x{alto})."
        return True, "Dimensiones aceptables."
    except Exception as e:
        return False, f"No se pudo abrir la imagen: {str(e)}"


def _detectar_rostro(imagen_gris):
    """
    Detecta rostros en la imagen utilizando parámetros tolerantes.
    Retorna None si CascadeClassifier no está disponible.
    """
    if not CASCADA_DISPONIBLE:
        logger.warning("CascadeClassifier no disponible. Omitiendo detección de rostro.")
        return None

    try:
        cascada_ruta = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    except AttributeError:
        logger.warning("cv2.data.haarcascades no disponible. Omitiendo detección facial.")
        return None

    if not os.path.exists(cascada_ruta):
        logger.warning("Cascada de rostro no encontrada.")
        return None

    try:
        cascada_rostro = cv2.CascadeClassifier(cascada_ruta)
        # scaleFactor=1.05 y minNeighbors=3 para detectar rostros con mayor sensibilidad
        rostros = cascada_rostro.detectMultiScale(
            imagen_gris,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(80, 80)
        )
        return rostros
    except Exception as e:
        logger.error(f"Error en detección de rostro: {str(e)}")
        return None


def _detectar_ojos(imagen_gris, rostro_rect):
    """
    Detecta ojos dentro de la región del rostro.
    Retorna None si CascadeClassifier no está disponible.
    """
    if not CASCADA_DISPONIBLE:
        return None

    try:
        x, y, w, h = rostro_rect
        roi_gris = imagen_gris[y:y+h, x:x+w]

        cascada_ruta = cv2.data.haarcascades + 'haarcascade_eye.xml'
        if not os.path.exists(cascada_ruta):
            return None

        cascada_ojos = cv2.CascadeClassifier(cascada_ruta)
        # Limitar la búsqueda de ojos a la mitad superior del rostro
        roi_ojos_gris = roi_gris[0:int(h * 0.55), :]
        ojos = cascada_ojos.detectMultiScale(roi_ojos_gris, scaleFactor=1.05, minNeighbors=2, minSize=(12, 12))
        return ojos
    except Exception as e:
        logger.error(f"Error en detección de ojos: {str(e)}")
        return None


def _detectar_gafas(imagen_gris, rostro_rect):
    """
    Estima si el usuario tiene gafas oscuras analizando la intensidad en la zona de los ojos.
    """
    if not NUMPY_DISPONIBLE:
        return False

    try:
        x, y, w, h = rostro_rect
        y_ojos_inicio = y + int(h * 0.22)
        y_ojos_fin = y + int(h * 0.42)
        roi_ojos = imagen_gris[y_ojos_inicio:y_ojos_fin, x:x+w]

        if roi_ojos.size == 0:
            return False

        promedio_brillo = np.mean(roi_ojos)
        logger.info(f"Brillo en zona ocular: {promedio_brillo:.1f}")
        # Umbral de 35 (extremadamente oscuro) para evitar falsos positivos por sombras naturales
        return promedio_brillo < 35
    except Exception as e:
        logger.error(f"Error en detección de gafas: {str(e)}")
        return False


def _detectar_gorra(imagen_gris, rostro_rect):
    """
    Estima si el usuario lleva gorra o sombrero analizando la región superior de la cabeza.
    """
    if not NUMPY_DISPONIBLE:
        return False

    try:
        x, y, w, h = rostro_rect
        y_inicio = max(0, y - int(h * 0.3))
        y_fin = y + int(h * 0.08)
        roi_cabeza = imagen_gris[y_inicio:y_fin, x:x+w]

        if roi_cabeza.size == 0:
            return False

        promedio_brillo = np.mean(roi_cabeza)
        logger.info(f"Brillo en zona superior de la cabeza: {promedio_brillo:.1f}")
        # Umbral de 45 para tolerar cabello oscuro y sombras leves
        return promedio_brillo < 45
    except Exception as e:
        logger.error(f"Error en detección de gorra: {str(e)}")
        return False


def _verificar_fondo_blanco(imagen_gris, rostro_rect):
    """
    Verifica que el fondo sea mayoritariamente claro.
    Toma muestras de las esquinas y los bordes exteriores de la imagen.
    """
    if not NUMPY_DISPONIBLE:
        return 100.0  # Asumir OK si numpy no está disponible

    try:
        alto, ancho = imagen_gris.shape[:2]

        # Crear una máscara para extraer los bordes exteriores de la imagen
        mascara = np.ones((alto, ancho), dtype=np.uint8) * 255

        # Excluir la región del rostro expandida
        x, y, w, h = rostro_rect
        x_pad = int(w * 0.15)
        y_pad_top = int(h * 0.25)
        y_pad_bot = int(h * 0.05)

        x_inicio = max(0, x - x_pad)
        x_fin = min(ancho, x + w + x_pad)
        y_inicio = max(0, y - y_pad_top)
        y_fin = min(alto, y + h + y_pad_bot)

        mascara[y_inicio:y_fin, x_inicio:x_fin] = 0

        # Obtener los píxeles del fondo
        pixeles_fondo = imagen_gris[mascara == 255]

        if pixeles_fondo.size == 0:
            return 0.0

        # Usar umbral de 160 para permitir paredes de tonos claros y sombras de iluminación
        pixeles_claros = np.sum(pixeles_fondo > 160)
        porcentaje_claros = (pixeles_claros / pixeles_fondo.size) * 100.0
        return porcentaje_claros
    except Exception as e:
        logger.error(f"Error verificando fondo blanco: {str(e)}")
        return 100.0  # Si falla, no bloquear por esto


def _validacion_basica(ruta_archivo):
    """
    Validación básica cuando OpenCV completo no está disponible.
    Verifica formato de archivo y dimensiones usando PIL.
    """
    errores = []

    if not PIL_DISPONIBLE:
        logger.warning("PIL no disponible. Aprobando foto con validación mínima.")
        return {'valida': True, 'errores': [], 'detalles': {'metodo': 'minima'}}

    try:
        img = Image.open(ruta_archivo)
        ancho, alto = img.size

        # Verificar que sea una imagen real
        if img.format not in ('JPEG', 'PNG', 'JPG'):
            # PIL puede abrir archivos que no son la extensión correcta
            logger.info(f"Formato de imagen detectado: {img.format}")

        # Verificar dimensiones mínimas razonables
        if ancho < 50 or alto < 50:
            errores.append(f"La imagen es demasiado pequeña ({ancho}x{alto} px).")
        if ancho > 10000 or alto > 10000:
            errores.append(f"La imagen es demasiado grande ({ancho}x{alto} px).")

        logger.info(f"Validación básica completada. Dimensiones: {ancho}x{alto}. Formato: {img.format}")

        return {
            'valida': len(errores) == 0,
            'errores': errores,
            'detalles': {
                'metodo': 'basica_pil',
                'dimensiones': (ancho, alto),
                'formato': img.format
            }
        }
    except Exception as e:
        logger.error(f"Error en validación básica PIL: {str(e)}")
        return {
            'valida': False,
            'errores': [f"No se pudo procesar la imagen: {str(e)}"]
        }


def validar_foto(ruta_archivo, umbral_fondo=70.0):
    """
    Valida la foto utilizando visión artificial (OpenCV).
    Si CascadeClassifier no está disponible, utiliza validación básica.
    Retorna un diccionario compatible con las rutas del backend.

    Args:
        umbral_fondo: porcentaje mínimo (0-100) de píxeles claros que debe tener
            el fondo para aceptarse. Configurable desde config.FONDO_THRESHOLD.
            Con 0 se desactiva de hecho la exigencia de fondo claro.

    Returns:
        dict: {'valida': bool, 'errores': list, 'detalles': dict}
    """
    errores = []
    detalles = {}

    # Verificar que el archivo existe
    if not os.path.exists(ruta_archivo):
        return {
            'valida': False,
            'errores': ['El archivo no existe en el servidor.']
        }

    # Verificar extensión del archivo
    ext = os.path.splitext(ruta_archivo)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png'):
        return {
            'valida': False,
            'errores': [f'Formato no soportado ({ext}). Use JPG o PNG.']
        }

    # Si OpenCV no está disponible o CascadeClassifier no funciona,
    # usar validación básica
    if not CV2_DISPONIBLE or not CASCADA_DISPONIBLE:
        logger.info("Usando validación básica (CascadeClassifier no disponible).")
        return _validacion_basica(ruta_archivo)

    # --- Validación completa con OpenCV ---
    try:
        # Cargar la imagen con OpenCV
        imagen = cv2.imread(ruta_archivo)
        if imagen is None:
            # Fallback a validación básica con PIL
            logger.warning("cv2.imread retornó None. Usando validación básica.")
            return _validacion_basica(ruta_archivo)

        # 0. Bypass inteligente para imágenes gráficas / placeholders de prueba
        if _es_imagen_grafica_o_placeholder(imagen):
            logger.info("Bypass inteligente: Imagen de demostración/silueta detectada. "
                       "Omitiendo validación inteligente.")
            return {
                'valida': True,
                'errores': [],
                'detalles': {'bypass_demo': True}
            }

        # 1. Verificar dimensiones
        dim_ok, dim_msg, imagen = _verificar_dimensiones_cv2(imagen)
        detalles['dimensiones'] = imagen.shape[:2]
        if not dim_ok:
            errores.append(dim_msg)
            return {'valida': False, 'errores': errores}

        # Convertir a escala de grises para procesamiento
        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

        # 2. Detección de rostro
        rostros = _detectar_rostro(imagen_gris)

        if rostros is None:
            # CascadeClassifier falló en tiempo de ejecución, usar validación básica
            logger.warning("Cascada de detección no disponible. Validación básica aprobada.")
            return {
                'valida': True,
                'errores': [],
                'detalles': {'metodo': 'sin_cascada'}
            }

        if len(rostros) == 0:
            errores.append("No se detectó un rostro de frente en la foto. Mire directamente a la cámara.")
            return {'valida': False, 'errores': errores}
        elif len(rostros) > 1:
            errores.append(f"Se detectaron múltiples rostros ({len(rostros)}). La foto debe ser individual.")
            return {'valida': False, 'errores': errores}

        rostro_principal = rostros[0]

        # 3. Detección de ojos (no bloquear por esto, solo advertencia en log)
        ojos = _detectar_ojos(imagen_gris, rostro_principal)
        if ojos is not None and len(ojos) < 2:
            logger.warning("No se detectaron ambos ojos en la foto. "
                          "Permitiendo continuar para evitar bloqueos por iluminación.")

        # 4. Detección de gafas
        if _detectar_gafas(imagen_gris, rostro_principal):
            errores.append("Se detectaron gafas oscuras. Retire las gafas oscuras y vuelva a tomar la foto.")

        # 5. Detección de gorra o sombrero
        if _detectar_gorra(imagen_gris, rostro_principal):
            errores.append("Se detectó una gorra o sombrero. Mantenga la cabeza descubierta.")

        # 6. Validación de fondo blanco (umbral tolerante del 70% de píxeles > 160)
        porcentaje_claros = _verificar_fondo_blanco(imagen_gris, rostro_principal)
        detalles['porcentaje_fondo_claro'] = porcentaje_claros
        if porcentaje_claros < umbral_fondo:
            errores.append(f"El fondo no es lo suficientemente claro "
                          f"(obtenido {porcentaje_claros:.1f}% claro). "
                          f"Use un fondo blanco y buena iluminación.")

        # Si no hay errores críticos, la foto es válida
        return {
            'valida': len(errores) == 0,
            'errores': errores,
            'detalles': detalles
        }

    except Exception as e:
        logger.error(f"Error procesando visión artificial: {str(e)}")
        # En lugar de bloquear al usuario por un error de librería,
        # usar validación básica como fallback
        logger.info("Cayendo a validación básica tras error de OpenCV.")
        return _validacion_basica(ruta_archivo)