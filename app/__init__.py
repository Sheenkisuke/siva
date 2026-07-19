"""
Fábrica de la aplicación Flask.
Configura e inicializa la aplicación y sus extensiones.
"""
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    """Crea y configura la aplicación Flask."""
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
    app = Flask(__name__, static_folder=static_folder)
    app.config.from_object(config_class)

    # Inicializar la base de datos
    db.init_app(app)

    # Configurar Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'

    # Registrar blueprints
    from app.routes import main
    app.register_blueprint(main)

    # Configurar registro de eventos (logging) a nivel INFO
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Asegurar que el directorio de subidas exista
    upload_path = os.path.join(app.root_path, '..', app.config['UPLOAD_FOLDER'])
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
        logging.info(f"Directorio de subidas creado en: {upload_path}")

    return app
