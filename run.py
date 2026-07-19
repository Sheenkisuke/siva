"""
Punto de entrada de la aplicación SIVA.
Crea la aplicación, inicializa la base de datos y ejecuta el servidor de desarrollo.
"""
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Crear tablas de la base de datos si no existen
        db.create_all()
    # Ejecutar en localhost puerto 5000 con modo debug activado
    app.run(host='127.0.0.1', port=5000, debug=True)
