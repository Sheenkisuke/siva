"""
Modelos de base de datos SQLAlchemy para la aplicación SIVA.
"""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class Usuario(UserMixin, db.Model):
    """Modelo de Usuario para el sistema de autenticación y datos personales."""
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(15), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.String(1), nullable=False) # 'M' o 'F'
    estado_civil = db.Column(db.String(20), nullable=False)
    foto_ruta = db.Column(db.String(200))
    huella_ruta = db.Column(db.String(200))
    firma_ruta = db.Column(db.String(200))
    contrasena_hash = db.Column(db.String(256), nullable=False)

    def verificar_contrasena(self, contrasena):
        """Verifica si la contraseña proporcionada coincide con el hash."""
        return check_password_hash(self.contrasena_hash, contrasena)

    def establecer_contrasena(self, contrasena):
        """Genera y guarda el hash de la contraseña."""
        self.contrasena_hash = generate_password_hash(contrasena)

    def get_id(self):
        """Devuelve el ID del usuario como cadena."""
        return str(self.id)

@login_manager.user_loader
def cargar_usuario(id_usuario):
    """Función de carga de usuario requerida por Flask-Login."""
    return Usuario.query.get(int(id_usuario))
