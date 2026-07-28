import qrcode
import json
import os
from io import BytesIO
from datetime import datetime


def sumar_anios(fecha, anios):
    """
    Suma años a una fecha de forma segura.

    Usar fecha.replace(year=...) directamente lanza ValueError cuando la fecha es
    el 29 de febrero y el año destino no es bisiesto. En ese caso se ajusta al
    28 de febrero (comportamiento estándar para vencimientos de documentos).
    """
    try:
        return fecha.replace(year=fecha.year + anios)
    except ValueError:
        return fecha.replace(year=fecha.year + anios, month=2, day=28)


def generar_qr(datos_usuario, ruta_salida=None):
    """
    Genera un código QR con los datos del usuario.
    
    Args:
        datos_usuario: dict with 'nombres', 'apellidos', 'cedula', 'fecha_nacimiento'
        ruta_salida: optional path to save QR image
    
    Returns:
        str or BytesIO: path to QR image or BytesIO object
    """
    hoy = datetime.now()
    vencimiento = sumar_anios(hoy, 10)

    contenido = {
        "sistema": "SIVA",
        "cedula": datos_usuario.get('cedula', ''),
        "nombres": datos_usuario.get('nombres', ''),
        "apellidos": datos_usuario.get('apellidos', ''),
        "fecha_nacimiento": datos_usuario.get('fecha_nacimiento', ''),
        "fecha_expedicion": hoy.strftime('%d/%m/%Y'),
        "valido_hasta": vencimiento.strftime('%d/%m/%Y')
    }
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    
    qr.add_data(json.dumps(contenido))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    if ruta_salida:
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
        img.save(ruta_salida)
        return ruta_salida
    else:
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
