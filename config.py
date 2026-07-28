import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración de la aplicación Flask."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-por-defecto'
    
    # --- RUTA DE BASE DE DATOS (CORREGIDA DEFINITIVAMENTE) ---
    # Obtener la ruta ABSOLUTA del proyecto
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Crear carpeta data/ si no existe
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    # Ruta absoluta al archivo de base de datos (con barra invertida para Windows)
    DB_PATH = os.path.join(DATA_DIR, 'database.db')
    # Usar la ruta absoluta con el formato correcto para SQLite
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH.replace(os.sep, "/")}'
    # --- FIN DE LA CORRECCIÓN ---
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'static/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Límite de 5MB
    # Umbral de similitud facial para aceptar (0.0-1.0). Configurable por entorno.
    FACIAL_THRESHOLD = float(os.environ.get('FACIAL_THRESHOLD', 0.85))
    # Tolerancia de distancia de face_recognition en el límite de coincidencia
    # (más bajo = más estricto). Se ancla al umbral en _distancia_a_similitud.
    FACIAL_TOLERANCE = float(os.environ.get('FACIAL_TOLERANCE', 0.6))
    # Porcentaje mínimo de píxeles claros que debe tener el fondo (0-100).
    # Configurable por variable de entorno FONDO_THRESHOLD. Para probar el
    # reconocimiento facial con fotos de fondo no blanco, bájelo (p. ej. 0).
    FONDO_THRESHOLD = float(os.environ.get('FONDO_THRESHOLD', 70.0))
    MAX_INTENTOS_FOTO = 3
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}