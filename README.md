# Proyecto SIVA (Sistema Inteligente de Verificación de Autenticidad)

SIVA es una aplicación web Flask para la renovación de la cédula de identidad venezolana. Integra validación de requisitos mediante IA y reconocimiento facial.

## Características

- Autenticación segura y control de sesiones
- Verificación facial usando DeepFace/OpenCV
- Validación de requisitos de fotografía
- Generación de cédula de identidad en formato PDF con ReportLab
- Generación y validación de códigos QR de identidad
- Interfaz moderna y responsiva

## Capturas de Pantalla

*(Aquí irían capturas de pantalla del sistema en funcionamiento)*

## Requisitos Previos

- Python 3.8+
- Bibliotecas descritas en `requirements.txt` (incluyendo Flask, SQLAlchemy, ReportLab, OpenCV, etc.)

## Instalación y Ejecución

1. Crear y activar entorno virtual:
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Inicializar la base de datos y usuarios de prueba:
   ```bash
   python init_db.py
   ```

4. Ejecutar la aplicación:
   ```bash
   flask run
   ```

## Usuarios de Prueba

La base de datos contiene los siguientes usuarios de prueba listos para iniciar sesión:

| # | Cédula | Contraseña |
|---|---|---|
| 1 | V-12345678 | carlos123 |
| 2 | V-23456789 | maria123 |
| 3 | V-34567890 | jose123 |
| 4 | V-45678901 | ana123 |
| 5 | V-56789012 | luis123 |
| 6 | V-67890123 | daniela123 |
| 7 | V-78901234 | pedro123 |
| 8 | V-89012345 | valentina123 |
| 9 | V-90123456 | andres123 |
| 10 | V-10234567 | sofia123 |

## Pruebas de IA (Reconocimiento Facial)

Para probar las características de Inteligencia Artificial:

1. Suba una foto real que cumpla con los requisitos.
2. Alternativamente, utilice las fotos de prueba en la carpeta `/test_photos/`.

**Nota sobre DeepFace y Reconocimiento Facial**: Como los usuarios generados utilizan siluetas como fotos placeholder (marcadores de posición), el comparador recurrirá al modo de simulación. Para una prueba real de IA, asegúrese de reemplazar la foto estática en `static/fotos/` del usuario correspondiente por una foto real y suba una foto similar.

## Estructura del Proyecto

```
SIVA/
├── app/                  # Aplicación Flask
│   ├── models/           # Modelos de base de datos
│   ├── routes/           # Rutas y controladores
│   ├── static/           # CSS, JS, Imágenes y recursos generados
│   ├── templates/        # Plantillas HTML (Jinja2)
│   └── utils/            # Utilidades (PDF, QR, IA, Validaciones)
├── tests/                # Pruebas unitarias
├── test_photos/          # Fotos de prueba para IA
├── init_db.py            # Script de inicialización de la BD
└── requirements.txt      # Dependencias
```

## Tecnologías Utilizadas

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login
- **Frontend:** HTML5, CSS3, JavaScript
- **Procesamiento PDF:** ReportLab
- **Códigos QR:** qrcode
- **Inteligencia Artificial / Visión por Computadora:** DeepFace, OpenCV
- **Manipulación de Imágenes:** Pillow (PIL)

## Licencia

Distribuido bajo la Licencia MIT.
