# Mapa de Archivos del Proyecto SIVA

Este documento contiene la clasificación completa de los archivos del sistema **SIVA (Sistema Inteligente de Verificación de Autenticidad)**, organizados por capas: **Backend**, **Frontend**, **Base de Datos** y **Configuraciones**.

---

## ⚙️ 1. CAPA DE BACKEND (Lógica y Controladores en Python)

Esta capa procesa las solicitudes, maneja la sesión del ciudadano, realiza el procesamiento de imágenes por visión artificial, genera los reportes y administra la comunicación interna del servidor.

### A. Inicialización y Rutas Principales
*   **[run.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/run.py)**
    *   *Función:* Es el punto de arranque de la aplicación. Crea el contexto del servidor web y ejecuta el entorno en modo de depuración (`debug=True`) en `http://127.0.0.1:5000`.
*   **[app/\_\_init\_\_.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/__init__.py)**
    *   *Función:* Define la fábrica de la aplicación Flask. Inicializa las extensiones de la base de datos (SQLAlchemy) y de la sesión (Flask-Login), registra el blueprint y asegura la creación del directorio para subir archivos de foto.
*   **[app/routes.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/routes.py)**
    *   *Función:* Contiene todos los controladores y las rutas URL de la aplicación web. Valida los inicios de sesión, gestiona las subidas de archivos, coordina las validaciones biométricas de fotos y controla las redirecciones y mensajes flash en la interfaz.

### B. Formularios y Modelos
*   **[app/forms.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/forms.py)**
    *   *Función:* Contiene funciones auxiliares para validar los campos del login, limpiar y formatear las cédulas agregando el prefijo oficial (ej: de `12345678` a `V-12345678`) y validar el tipo de archivo y tamaño de la foto antes de enviarla a procesar.
*   **[app/models.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/models.py)**
    *   *Función:* Mapea la tabla `usuarios` utilizando SQLAlchemy. Almacena las variables de cada ciudadano y expone funciones seguras para hashear y verificar las contraseñas.

### C. Utilidades y Visión Artificial (Carpeta `app/utils/`)
*   **[app/utils/\_\_init\_\_.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/__init__.py)**
    *   *Función:* Convierte el directorio de utilidades en un paquete de Python importable.
*   **[app/utils/photo_validator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/photo_validator.py)**
    *   *Función:* Validador de requisitos de fotos usando OpenCV y PIL. Se encarga de comprobar el fondo blanco/claro, dimensiones y proporciones de imagen, y maneja las excepciones y fallbacks si el sistema no posee detectores en cascada facial.
*   **[app/utils/face_comparator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/face_comparator.py)**
    *   *Función:* Comparador facial biométrico. Utiliza `DeepFace` y `face_recognition` de forma adaptativa. Si no están instaladas, ejecuta una comparación por histogramas de color en canal HSV, simulando la aceptación inteligente con personas y bloqueando fotos de mascotas/perros.
*   **[app/utils/pdf_generator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/pdf_generator.py)**
    *   *Función:* Crea el documento PDF vectorial de la cédula de identidad en tamaño carta con el anverso y reverso listos para recortar y plastificar, insertando fotos, firmas y huellas reales.
*   **[app/utils/qr_generator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/qr_generator.py)**
    *   *Función:* Codifica un JSON estructurado con los datos del ciudadano, la fecha de emisión y vencimiento dentro de un código QR PNG para colocarlo en el reverso del PDF.

---

## 🎨 2. CAPA DE FRONTEND (Plantillas y Archivos Estáticos)

Esta capa define todo el diseño visual, la interactividad cliente-servidor, los formularios dinámicos y la interfaz adaptativa para celulares y computadoras.

### A. Plantillas HTML (Carpeta `app/templates/`)
*   **[app/templates/base.html](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/templates/base.html)**
    *   *Función:* Es el diseño esqueleto común. Importa las tipografías de Google y las hojas de estilos. Dibuja la barra de menú lateral (sidebar) con la foto y cédula del ciudadano logueado y el contenedor de mensajes de alerta.
*   **[app/templates/login.html](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/templates/login.html)**
    *   *Función:* Vista de inicio de sesión con el formulario de credenciales y la ventana modal informativa para recuperar contraseñas a través de la oficina del SAIME.
*   **[app/templates/dashboard.html](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/templates/dashboard.html)**
    *   *Función:* Panel ciudadano de bienvenida. Dibuja los accesos directos a los trámites del portal (renovación de cédula y pasaporte) y muestra un resumen con los datos actuales del usuario.
*   **[app/templates/renovacion.html](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/templates/renovacion.html)**
    *   *Función:* Muestra los datos de identidad que van a ser impresos en la cédula, la foto histórica actual en el sistema y los registros de firma y huella digital del ciudadano.
*   **[app/templates/subir_foto.html](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/templates/subir_foto.html)**
    *   *Función:* Interfaz de carga fotográfica con los requisitos solicitados por el SAIME. Incluye una zona interactiva para arrastrar archivos e indica visualmente el número de intentos restantes.
*   **[app/templates/exito.html](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/templates/exito.html)**
    *   *Función:* Muestra la confirmación de la renovación, el porcentaje de coincidencia biométrica y una simulación interactiva de la nueva cédula digital. Contiene los botones de descarga de PDF.
*   **[app/templates/pasaporte.html](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/templates/pasaporte.html)**
    *   *Función:* Vista informativa que se muestra cuando el usuario intenta acceder a la sección de pasaportes.

### B. Archivos Estáticos (Carpeta `static/`)
*   **[static/css/style.css](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/static/css/style.css)**
    *   *Función:* Contiene todas las reglas de estilo CSS de la aplicación (variables de colores venezolanos, panel translúcido de glassmorphism, formularios, alertas dinámicas y reglas responsivas para móviles).
*   **[static/js/main.js](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/static/js/main.js)**
    *   *Función:* Añade interactividad al cliente: controla la apertura del menú móvil, el desvanecimiento automático de alertas tras 5 segundos, la previsualización inmediata de la foto seleccionada y el disparo del panel de carga de "Verificando identidad..." durante el submit del formulario.

---

## 💾 3. CAPA DE DATOS (Base de Datos y Archivos de Carga)

Esta capa se encarga del almacenamiento físico estructurado de los registros de los ciudadanos y de guardar los archivos subidos al portal de forma ordenada.

### A. Base de Datos SQLite
*   **[data/database.db](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/data/database.db)** *(Creado en la instalación)*
    *   *Función:* El archivo físico de base de datos relacional de SQLite. Almacena la tabla `usuarios` y todos sus registros persistentes.
*   **[init_db.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/init_db.py)**
    *   *Función:* Script para limpiar, crear las tablas del esquema en la base de datos e insertar los datos iniciales de los 10 ciudadanos de prueba.

### B. Directorios de Archivos e Imágenes
*   **`static/fotos/`**: Aloja las imágenes autogeneradas de los rostros/avatares silueta de los 10 ciudadanos para la base de datos de prueba.
*   **`static/firmas/`**: Aloja los trazos/firmas digitalizadas individuales de los 10 usuarios para el PDF.
*   **`static/huellas/`**: Aloja las huellas dactilares digitalizadas de los 10 usuarios.
*   **`static/img/bandera.png`**: Contiene la bandera nacional de Venezuela en 3 franjas de color utilizada en el login y en el carnet digital.
*   **`uploads/`**: Carpeta temporal en la raíz que se crea automáticamente al subir fotos. Guarda las imágenes enviadas por los usuarios de forma segura y los PDFs generados para que puedan ser descargados de inmediato.

---

## 🛠️ 4. CONFIGURACIONES GENERALES (Raíz del Proyecto)

*   **[requirements.txt](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/requirements.txt)**
    *   *Función:* Lista de paquetes y dependencias del sistema de desarrollo listos para ser instalados mediante `pip install -r requirements.txt`.
*   **[.env](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/.env)**
    *   *Función:* Almacena las variables de entorno locales de configuración externa.
*   **[README.md](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/README.md)**
    *   *Función:* Archivo de documentación y presentación general del proyecto para desarrolladores. Contiene la lista de usuarios y contraseñas de acceso de prueba.
