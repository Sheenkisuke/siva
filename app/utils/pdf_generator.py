import os
import logging
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import cm
from app.utils.qr_generator import generar_qr, sumar_anios

logger = logging.getLogger(__name__)

def generar_cedula_pdf(usuario, ruta_foto_nueva, ruta_salida):
    """
    Genera un PDF con el diseño de cédula venezolana.
    
    Args:
        usuario: objeto Usuario con todos los datos
        ruta_foto_nueva: ruta a la nueva foto del usuario
        ruta_salida: ruta donde guardar el PDF
    
    Returns:
        str: ruta al PDF generado
    """
    try:
        # Asegurar que el directorio exista
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
        
        # Crear canvas
        c = canvas.Canvas(ruta_salida, pagesize=letter)
        
        # Dimensiones de la tarjeta: 8.9 cm x 5.4 cm
        ancho_tarjeta = 8.9 * cm
        alto_tarjeta = 5.4 * cm
        
        # Posición inicial
        x_anverso = 2 * cm
        y_tarjeta = 20 * cm
        x_reverso = x_anverso + ancho_tarjeta + 1 * cm
        
        # --- ANVERSO ---
        # Fondo
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.rect(x_anverso, y_tarjeta, ancho_tarjeta, alto_tarjeta, stroke=1, fill=0)
        
        # Barra superior azul (#003DA5)
        c.setFillColorRGB(0.0, 0.24, 0.65)
        c.rect(x_anverso, y_tarjeta + alto_tarjeta - 0.8 * cm, ancho_tarjeta, 0.8 * cm, stroke=0, fill=1)
        
        # Texto superior
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 6)
        c.drawString(x_anverso + 0.5 * cm, y_tarjeta + alto_tarjeta - 0.4 * cm, "REPÚBLICA BOLIVARIANA DE VENEZUELA")
        
        # Título cédula
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 5)
        c.drawString(x_anverso + 3 * cm, y_tarjeta + alto_tarjeta - 1.2 * cm, "CÉDULA DE IDENTIDAD")
        
        # Foto del usuario
        try:
            c.drawImage(ruta_foto_nueva, x_anverso + 0.2 * cm, y_tarjeta + 1.2 * cm, width=2.5*cm, height=3*cm)
        except Exception as e:
            logger.warning(f"No se pudo cargar la foto: {e}")
            c.rect(x_anverso + 0.2 * cm, y_tarjeta + 1.2 * cm, 2.5*cm, 3*cm)
            
        # Datos del usuario
        c.setFont("Helvetica", 5)
        y_datos = y_tarjeta + alto_tarjeta - 1.8 * cm
        c.drawString(x_anverso + 3 * cm, y_datos, f"Apellidos: {usuario.apellidos}")
        c.drawString(x_anverso + 3 * cm, y_datos - 0.4 * cm, f"Nombres: {usuario.nombres}")
        c.drawString(x_anverso + 3 * cm, y_datos - 0.8 * cm, f"Cédula: {usuario.cedula}")
        c.drawString(x_anverso + 3 * cm, y_datos - 1.2 * cm, f"Fecha Nac: {usuario.fecha_nacimiento.strftime('%d/%m/%Y') if hasattr(usuario.fecha_nacimiento, 'strftime') else usuario.fecha_nacimiento}")
        c.drawString(x_anverso + 3 * cm, y_datos - 1.6 * cm, f"Sexo: {usuario.sexo}")
        c.drawString(x_anverso + 3 * cm, y_datos - 2.0 * cm, f"Estado Civil: {usuario.estado_civil}")
        
        # Fechas de expedición y vencimiento
        hoy = datetime.now()
        vencimiento = sumar_anios(hoy, 10)
        
        c.setFont("Helvetica", 4)
        c.drawString(x_anverso + 3 * cm, y_tarjeta + 0.3 * cm, f"Fecha Expedición: {hoy.strftime('%d/%m/%Y')}")
        c.drawString(x_anverso + 5.5 * cm, y_tarjeta + 0.3 * cm, f"Fecha Vencimiento: {vencimiento.strftime('%d/%m/%Y')}")
        
        # Firma y Huella
        from flask import current_app
        try:
            ruta_firma = os.path.join(current_app.static_folder, usuario.firma_ruta) if usuario.firma_ruta else None
            if ruta_firma and os.path.exists(ruta_firma):
                c.drawImage(ruta_firma, x_anverso + 0.2 * cm, y_tarjeta + 0.2 * cm, width=2.5*cm, height=0.8*cm)
        except Exception as e:
            logger.warning(f"No se pudo cargar la firma: {e}")

        try:
            ruta_huella = os.path.join(current_app.static_folder, usuario.huella_ruta) if usuario.huella_ruta else None
            if ruta_huella and os.path.exists(ruta_huella):
                c.drawImage(ruta_huella, x_anverso + 7 * cm, y_tarjeta + 1 * cm, width=1.5*cm, height=2*cm)
        except Exception as e:
            logger.warning(f"No se pudo cargar la huella: {e}")

        # --- REVERSO ---
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.rect(x_reverso, y_tarjeta, ancho_tarjeta, alto_tarjeta, stroke=1, fill=0)
        
        # Barra superior reverso
        c.setFillColorRGB(0.0, 0.24, 0.65)
        c.rect(x_reverso, y_tarjeta + alto_tarjeta - 0.8 * cm, ancho_tarjeta, 0.8 * cm, stroke=0, fill=1)
        
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_reverso + 4 * cm, y_tarjeta + alto_tarjeta - 0.5 * cm, "SAIME")
        
        # QR
        c.setFillColorRGB(0, 0, 0)
        datos_qr = {
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "cedula": usuario.cedula,
            "fecha_nacimiento": usuario.fecha_nacimiento.strftime('%d/%m/%Y') if hasattr(usuario.fecha_nacimiento, 'strftime') else str(usuario.fecha_nacimiento)
        }
        
        try:
            ruta_qr = os.path.join(os.path.dirname(ruta_salida), f"qr_{usuario.cedula}.png")
            generar_qr(datos_qr, ruta_qr)
            c.drawImage(ruta_qr, x_reverso + 3 * cm, y_tarjeta + 1.5 * cm, width=3*cm, height=3*cm)
            if os.path.exists(ruta_qr):
                os.remove(ruta_qr)
        except Exception as e:
            logger.warning(f"Error al generar QR: {e}")
            c.rect(x_reverso + 3 * cm, y_tarjeta + 1.5 * cm, 3*cm, 3*cm)
            
        c.setFont("Helvetica", 5)
        c.drawCentredString(x_reverso + ancho_tarjeta/2, y_tarjeta + 1 * cm, "Escanee para verificar")
        c.drawCentredString(x_reverso + ancho_tarjeta/2, y_tarjeta + 0.5 * cm, "Servicio Administrativo de Identificación, Migración y Extranjería")
        c.setFont("Helvetica", 4)
        c.drawCentredString(x_reverso + ancho_tarjeta/2, y_tarjeta + 0.2 * cm, "Documento válido en todo el territorio nacional")
        
        c.save()
        return ruta_salida
        
    except Exception as e:
        logger.error(f"Error generando PDF de cédula: {e}")
        return None

def generar_pdf(usuario, ruta_foto_nueva):
    """
    Función wrapper compatible con routes.py.
    Calcula automáticamente la ruta de salida en el directorio de subidas.
    """
    from flask import current_app
    upload_folder = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'])
    ruta_salida = os.path.join(upload_folder, f"cedula_{usuario.cedula}.pdf")
    return generar_cedula_pdf(usuario, ruta_foto_nueva, ruta_salida)

