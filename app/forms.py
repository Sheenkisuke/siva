"""
Funciones de ayuda para la validación de formularios simples.
"""
import os
from flask import current_app

def validar_login(cedula, contrasena):
    """
    Valida que los datos de login estén presentes.
    No verifica credenciales reales aquí.
    """
    if not cedula or not contrasena:
        return False, "La cédula y la contraseña son obligatorias."
    return True, ""

def validar_archivo_foto(archivo):
    """
    Verifica que la extensión y el tamaño del archivo subido sean válidos.
    (El tamaño se maneja principalmente mediante MAX_CONTENT_LENGTH en Flask).
    """
    if not archivo or archivo.filename == '':
        return False, "No se seleccionó ningún archivo."
        
    extensiones_permitidas = current_app.config['ALLOWED_EXTENSIONS']
    if not ('.' in archivo.filename and \
           archivo.filename.rsplit('.', 1)[1].lower() in extensiones_permitidas):
        return False, "Tipo de archivo no permitido. Solo se aceptan PNG, JPG, JPEG."
        
    return True, ""

def formatear_cedula(cedula):
    """
    Asegura que la cédula tenga el formato V-12345678.
    """
    cedula = str(cedula).strip().upper()
    if not cedula.startswith('V-') and not cedula.startswith('E-'):
        if cedula.isdigit():
            return f"V-{cedula}"
    return cedula
