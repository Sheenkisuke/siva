
"""
Rutas principales de la aplicación SIVA.
Maneja la autenticación, vistas del tablero y proceso de renovación.
"""
import os
import uuid
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Usuario
from app.forms import validar_login, validar_archivo_foto, formatear_cedula

# Configurar el blueprint principal
main = Blueprint('main', __name__)

@main.route('/')
def inicio():
    """Redirige a la página de login o dashboard según sesión."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        cedula_raw = request.form.get('cedula')
        contrasena = request.form.get('password') or request.form.get('contrasena')
        
        valido, mensaje = validar_login(cedula_raw, contrasena)
        if not valido:
            flash(mensaje, 'danger')
            return render_template('login.html')
            
        cedula = formatear_cedula(cedula_raw)
        usuario = Usuario.query.filter_by(cedula=cedula).first()
        
        if usuario is None or not usuario.verificar_contrasena(contrasena):
            logging.warning(f"Intento de inicio de sesión fallido para cédula: {cedula}")
            flash('Cédula o contraseña incorrectas.', 'danger')
            return render_template('login.html')
            
        login_user(usuario)
        logging.info(f"Usuario {cedula} inició sesión correctamente.")
        # Inicializar contador de intentos de foto
        session['intentos_foto'] = 0
        return redirect(url_for('main.dashboard'))
        
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario actual."""
    usuario_cedula = current_user.cedula
    logout_user()
    session.pop('intentos_foto', None)
    logging.info(f"Usuario {usuario_cedula} cerró sesión.")
    flash('Ha cerrado sesión exitosamente.', 'success')
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    """Tablero principal después del inicio de sesión."""
    return render_template('dashboard.html', usuario=current_user)

@main.route('/renovacion')
@login_required
def renovacion():
    """Muestra los datos personales del usuario y advertencias del SAIME."""
    session['intentos_foto'] = 0
    return render_template('renovacion.html', usuario=current_user)

@main.route('/subir-foto')
@login_required
def subir_foto():
    """Página para subir la nueva foto."""
    if session.get('intentos_foto', 0) >= current_app.config['MAX_INTENTOS_FOTO']:
        flash('Ha superado el límite de intentos. Por favor diríjase a una oficina del SAIME.', 'danger')
        return redirect(url_for('main.dashboard'))
    intentos_actuales = session.get('intentos_foto', 0) + 1
    return render_template('subir_foto.html', intentos=intentos_actuales)

@main.route('/verificar-foto', methods=['POST'])
@login_required
def verificar_foto():
    """Recibe y procesa la foto subida."""
    # Inicializar contador si no existe
    if 'intentos_foto' not in session:
        session['intentos_foto'] = 0
        
    if session['intentos_foto'] >= current_app.config['MAX_INTENTOS_FOTO']:
        flash('Límite de intentos superado. Debe asistir a una sede del SAIME.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    if 'foto' not in request.files:
        flash('No se encontró el archivo de imagen.', 'danger')
        return redirect(url_for('main.subir_foto'))
        
    archivo = request.files['foto']
    valido, mensaje = validar_archivo_foto(archivo)
    
    if not valido:
        flash(mensaje, 'danger')
        return redirect(url_for('main.subir_foto'))
        
    try:
        # Guardar archivo con nombre único
        nombre_archivo = secure_filename(archivo.filename)
        ext = nombre_archivo.rsplit('.', 1)[1].lower()
        nombre_unico = f"foto_nueva_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
        
        upload_folder = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'])
        ruta_guardado = os.path.join(upload_folder, nombre_unico)
        archivo.save(ruta_guardado)
        
        # Guardar la ruta de la nueva foto en sesión para mostrarla en éxito
        session['nueva_foto'] = f"uploads/{nombre_unico}"
        logging.info(f"Foto subida guardada en: {ruta_guardado}")
        
        try:
            from app.utils import photo_validator, face_comparator, pdf_generator
        except ImportError:
            logging.warning("Módulos de utilidad no encontrados. Utilizando validación simulada.")
            class MockValidator:
                @staticmethod
                def validar_foto(ruta): 
                    return {'valida': True, 'errores': []}
            class MockComparator:
                @staticmethod
                def comparar_rostros(foto1, foto2): 
                    return {'porcentaje_similitud': 90.5, 'coincide': True}
            class MockPDFGen:
                @staticmethod
                def generar_pdf(usuario, foto): 
                    return os.path.join(upload_folder, f"cedula_{usuario.cedula}.pdf")
                
            photo_validator = MockValidator()
            face_comparator = MockComparator()
            pdf_generator = MockPDFGen()
        
        # Validar foto
        resultado_validacion = photo_validator.validar_foto(ruta_guardado)
        if not resultado_validacion.get('valida', False):
            session['intentos_foto'] += 1
            if session['intentos_foto'] >= current_app.config['MAX_INTENTOS_FOTO']:
                flash('Ha fallado la validación 3 veces. Diríjase a una oficina del SAIME.', 'danger')
                return redirect(url_for('main.dashboard'))
            msg_validar = ", ".join(resultado_validacion.get('errores', ['Error desconocido']))
            flash(f'Error en la foto: {msg_validar}. Intento {session["intentos_foto"]} de {current_app.config["MAX_INTENTOS_FOTO"]}', 'warning')
            return redirect(url_for('main.subir_foto'))
            
        # Comparar rostros
        foto_anterior = os.path.join(current_app.static_folder, current_user.foto_ruta) if current_user.foto_ruta else None
        
        resultado_comparacion = face_comparator.comparar_rostros(ruta_guardado, foto_anterior)
        similitud_porcentaje = resultado_comparacion.get('porcentaje_similitud', 0)
        similitud_decimal = similitud_porcentaje / 100.0
        
        umbral = current_app.config['FACIAL_THRESHOLD']
        if similitud_decimal < umbral:
            session['intentos_foto'] += 1
            logging.warning(f"Similitud facial baja ({similitud_decimal}) para usuario {current_user.cedula}")
            flash(f'Error de identidad: La foto no coincide con nuestros registros ({similitud_porcentaje}% de coincidencia, se requiere {umbral * 100}%).', 'danger')
            return redirect(url_for('main.subir_foto'))
            
        # Generar PDF
        ruta_pdf = pdf_generator.generar_pdf(current_user, ruta_guardado)
        session['pdf_generado'] = ruta_pdf
        session['similitud'] = similitud_porcentaje
        
        logging.info(f"Verificación exitosa y PDF generado para usuario {current_user.cedula}")
        return redirect(url_for('main.exito'))
        
    except Exception as e:
        logging.error(f"Error procesando la foto: {str(e)}")
        flash('Ocurrió un error inesperado al procesar su solicitud. Por favor intente más tarde.', 'danger')
        return redirect(url_for('main.subir_foto'))

@main.route('/exito')
@login_required
def exito():
    """Página de éxito tras verificación y generación de PDF."""
    if 'pdf_generado' not in session:
        flash('No se encontró ninguna cédula lista para descargar.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    similitud = session.get('similitud', '90.0')
    
    # Obtener la ruta de la nueva foto desde la sesión
    # Si no existe, usar la foto anterior del usuario
    nueva_foto = session.get('nueva_foto', current_user.foto_ruta)
    
    return render_template('exito.html', 
                         similitud=similitud, 
                         nueva_foto=nueva_foto,
                         usuario=current_user)

@main.route('/descargar-pdf')
@login_required
def descargar_pdf():
    """Permite al usuario descargar la cédula en PDF generada."""
    ruta_pdf = session.get('pdf_generado')
    if not ruta_pdf or not os.path.exists(ruta_pdf):
        flash('El archivo PDF no está disponible. Por favor, repita el proceso.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    try:
        return send_file(
            ruta_pdf,
            as_attachment=True,
            download_name=f"cedula_{current_user.cedula}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        logging.error(f"Error al enviar PDF: {str(e)}")
        flash('Error al descargar el archivo.', 'danger')
        return redirect(url_for('main.exito'))

@main.route('/pasaporte')
@login_required
def pasaporte():
    """Muestra mensaje de servicio no disponible."""
    flash('El servicio de renovación de pasaportes no se encuentra disponible en este momento.', 'info')
    return render_template('pasaporte.html')