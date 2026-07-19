# Arquitectura, Tecnologías y Estructura del Código SIVA

Este documento detalla el ecosistema tecnológico utilizado en **SIVA (Sistema Inteligente de Verificación de Autenticidad)**, dónde se implementa cada tecnología y una guía completa archivo por archivo para saber qué contiene y cómo se puede modificar cada uno.

---

## 🛠️ 1. Stack Tecnológico y Uso en el Código

SIVA está construido sobre un stack de desarrollo web moderno, ligero y eficiente en Python:

### A. Core Backend
*   **Flask (v3.1.3):** El micro-framework web de Python. Es el corazón del servidor. Maneja el enrutamiento HTTP, sesiones de usuario y el ciclo de vida de la aplicación.
    *   *Uso principal:* En [app/routes.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/routes.py) (definición de endpoints y lógica de negocio) y [app/\_\_init\_\_.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/__init__.py) (fábrica de creación de la app).
*   **Flask-Login (v0.6.3):** Gestiona las sesiones activas de usuario, cookies de inicio de sesión, protección de rutas mediante `@login_required` y recuperación del usuario conectado con `current_user`.
    *   *Uso principal:* Configurado en [app/\_\_init\_\_.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/__init__.py) y utilizado a lo largo de las rutas de verificación en [app/routes.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/routes.py).
*   **Werkzeug (v3.1.8):** Utilidad WSGI interna de Flask que provee herramientas de seguridad para el hash de contraseñas (`generate_password_hash`, `check_password_hash`) y subida segura de nombres de archivo (`secure_filename`).
    *   *Uso principal:* En el modelo de base de datos [app/models.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/models.py) y en el procesamiento de carga de fotos en [app/routes.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/routes.py).

### B. Base de Datos y Persistencia
*   **SQLite:** Motor de base de datos relacional ligero basado en archivos (no requiere instalar un servidor externo).
    *   *Uso principal:* El archivo físico se crea automáticamente en `data/database.db`.
*   **SQLAlchemy y Flask-SQLAlchemy (v3.1.1):** ORM (Object-Relational Mapping) para mapear tablas SQL a objetos de Python, facilitando la interacción con la base de datos sin escribir sentencias SQL manuales.
    *   *Uso principal:* Definición del esquema de la tabla de ciudadanos en [app/models.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/models.py).

### C. Visión Artificial y Procesamiento de Imagen
*   **OpenCV Headless (v5.0.0.93 / v4.x):** Biblioteca líder en visión computacional. Procesa la matriz de píxeles para análisis espacial y cromático.
    *   *Uso principal:* [photo_validator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/photo_validator.py) (detección de fondos, brillo ocular, gorras) y [face_comparator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/face_comparator.py) (cálculo de histogramas HSV y correlación de colores de las fotos).
*   **Pillow (v12.3.0):** Librería para procesamiento básico de imágenes en Python (creación, escritura de fuentes, trazado gráfico).
    *   *Uso principal:* Utilizado en [init_db.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/init_db.py) para autogenerar las siluetas, firmas escritas y huellas dactilares de prueba.
*   **DeepFace y face_recognition:** (Opcionales / Carga adaptativa) Bibliotecas de deep learning para reconocimiento facial avanzado basadas en TensorFlow.
    *   *Uso principal:* Mapeadas con manejo de importación dinámica en [face_comparator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/face_comparator.py) para conmutar a simulación inteligente por histogramas en entornos donde no estén compiladas.

### D. Generación de Documentación y Reportes
*   **ReportLab (v5.0.0):** Generador de archivos PDF vectoriales de alta precisión a partir de coordenadas.
    *   *Uso principal:* En [pdf_generator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/pdf_generator.py) para maquetar el anverso y reverso de la cédula digital.
*   **Qrcode (v8.2):** Generador de códigos QR bidimensionales.
    *   *Uso principal:* En [qr_generator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/qr_generator.py) para codificar los datos del ciudadano en formato JSON dentro del carnet.

---

## 📂 2. Estructura de Archivos: Contenido y Qué Modificar

### A. Archivos de Configuración e Inicio (Raíz)

#### 1. [config.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/config.py)
*   **¿Qué contiene?**: Las variables globales del servidor (clave secreta de Flask, ruta absoluta de la base de datos, límite de peso del archivo de 5MB, umbral de aceptación facial de 85% y máximo de 3 intentos).
*   **¿Qué se puede modificar?**:
    *   `FACIAL_THRESHOLD`: Modificar el porcentaje mínimo de similitud requerido para aprobar al usuario (ej: bajar de `0.85` a `0.70`).
    *   `MAX_INTENTOS_FOTO`: Incrementar o disminuir el número de intentos permitidos antes de bloquear la renovación (ej: cambiar `3` por `5`).
    *   `SECRET_KEY`: Cambiar la cadena de encriptación de cookies y sesiones para mejorar la seguridad en producción.

#### 2. [run.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/run.py)
*   **¿Qué contiene?**: Punto de entrada de Python. Ejecuta el inicializador de base de datos al vuelo y corre el servidor Flask.
*   **¿Qué se puede modificar?**:
    *   El puerto de red (por defecto `5000`) o la dirección IP (`host='127.0.0.1'`). Si deseas que el proyecto sea accesible desde otros dispositivos conectados al mismo Wi-Fi, cámbialo a `host='0.0.0.0'`.

#### 3. [init_db.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/init_db.py)
*   **¿Qué contiene?**: Script para borrar la base de datos y recrear las tablas, poblando 10 registros ficticios con contraseñas hasheadas y autogenerando imágenes para simular firmas, fotos y huellas dactilares usando `Pillow`.
*   **¿Qué se puede modificar?**:
    *   `usuarios_data`: Modificar nombres, apellidos, fechas de nacimiento o contraseñas por defecto de los ciudadanos de prueba.
    *   Los colores de fondo y dimensiones de los placeholders autogenerados.

---

### B. Lógica y Rutas (Backend - Carpeta `app/`)

#### 1. [app/\_\_init\_\_.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/__init__.py)
*   **¿Qué contiene?**: Fábrica de la aplicación. Enlaza Flask con la base de datos SQLAlchemy, inicializa Flask-Login y registra el Blueprint principal (`main`).
*   **¿Qué se puede modificar?**:
    *   Añadir nuevas extensiones de Flask (ej. Flask-Mail, Flask-Migrate).
    *   Modificar el mensaje por defecto que muestra Flask al intentar acceder a rutas protegidas (`login_manager.login_message`).

#### 2. [app/models.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/models.py)
*   **¿Qué contiene?**: Definición de la tabla `usuarios` mapeada a la clase `Usuario`. Expone campos de cédula, nombres, apellidos, fecha de nacimiento, estado civil, sexo, contraseñas hasheadas y las rutas de sus huellas, firmas y fotos.
*   **¿Qué se puede modificar?**:
    *   Agregar nuevos campos a la base de datos del ciudadano (ej. `direccion = db.Column(db.String(200))`, `telefono = db.Column(db.String(20))`).
    *   *Nota:* Si modificas los campos de este archivo, deberás borrar la base de datos física local (`data/database.db`) y volver a ejecutar `python init_db.py` para recrear las tablas con los nuevos campos.

#### 3. [app/forms.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/forms.py)
*   **¿Qué contiene?**: Lógica helper de formateo de texto y validación de extensiones de archivos.
*   **¿Qué se puede modificar?**:
    *   `validar_archivo_foto`: Permitir nuevas extensiones de archivos (ej: admitir formatos `.webp` o `.bmp`).
    *   `formatear_cedula`: Modificar las restricciones de entrada o sanitización del formato del campo Cédula.

#### 4. [app/routes.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/routes.py)
*   **¿Qué contiene?**: Todo el ruteo lógico del servidor: `/login`, `/logout`, `/dashboard`, `/renovacion`, `/subir-foto`, `/verificar-foto`, `/exito`, `/descargar-pdf` y `/pasaporte`.
*   **¿Qué se puede modificar?**:
    *   Lógica tras una verificación exitosa: qué datos guardar en la sesión o cómo renombrar los archivos subidos.
    *   Redirecciones, mensajes informativos en pantalla (con `flash()`), o restricciones de acceso.

---

### C. Herramientas de Procesamiento (Carpeta `app/utils/`)

#### 1. [app/utils/photo_validator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/photo_validator.py)
*   **¿Qué contiene?**: Validador de fotografía. Utiliza OpenCV para evaluar el color del fondo de la imagen, verificar el tamaño (336x448 px), brillo de ojos, detectar gorras o anteojos oscuros. Contiene el bypass para placeholders de desarrollo.
*   **¿Qué se puede modificar?**:
    *   El porcentaje mínimo de píxeles claros requerido para el fondo (`porcentaje_claros < 70.0`).
    *   El umbral de detección de color para gafas oscuras y gorras (cambiando los umbrales de brillo promedio `35` y `45`).

#### 2. [app/utils/face_comparator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/face_comparator.py)
*   **¿Qué contiene?**: Comparador biométrico. Contiene la lógica para invocar a `DeepFace` o `face_recognition` y el fallback basado en correlación de histogramas HSV para una simulación real de colores en local sin librerías pesadas.
*   **¿Qué se puede modificar?**:
    *   El modelo utilizado de DeepFace (ej: cambiar `"VGG-Face"` por `"Facenet512"` o `"ArcFace"`).
    *   Modificar las palabras clave que disparan el rechazo automático de mascotas/perros (como añadir `"gato"`, `"paisaje"`, etc.).
    *   Cambiar los porcentajes simulados o el comportamiento de la comparación HSV.

#### 3. [app/utils/pdf_generator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/pdf_generator.py)
*   **¿Qué contiene?**: Generador del PDF físico de la cédula venezolana utilizando ReportLab. Ubica las posiciones exactas de firmas, huellas, fotos, QR y datos escritos en el anverso y reverso.
*   **¿Qué se puede modificar?**:
    *   Posición, tamaño y alineación de los textos e imágenes.
    *   Los colores de las barras superior e inferior y los textos del Ministerio/SAIME (ver la guía específica de PDF).
    *   Fecha de expiración de la cédula (cambiar `10` años a `15` años).

#### 4. [app/utils/qr_generator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/qr_generator.py)
*   **¿Qué contiene?**: Generador de códigos QR codificando datos del ciudadano en formato JSON.
*   **¿Qué se puede modificar?**:
    *   Los campos que se encriptan o codifican dentro del QR (ej. agregar el estado civil, fecha de vencimiento, etc.).

---

### D. Interfaz Gráfica (Frontend - Carpeta `app/templates/` y `static/`)

#### 1. Carpetas `static/css/style.css` y `static/js/main.js`
*   **¿Qué contienen?**: La hoja de estilos CSS general (diseño responsivo con glassmorphism, degradados venezolanos, loaders) y el archivo de scripts JS para manejar vistas previas dinámicas, drag & drop, diálogos modales y animaciones.
*   **¿Qué se puede modificar?**:
    *   Cambiar los colores base modificando las variables del `:root` en CSS (ej: `--primary-blue`, `--dark-bg`, etc.).
    *   Personalizar la animación del Spinner de carga en JS o el tiempo en que desaparecen las alertas (`setTimeout(dismissAlert, 5000)`).

#### 2. Plantillas HTML (`app/templates/`)
*   **base.html**: Estructura global. Contiene el sidebar con la foto y datos del usuario logueado, y el contenedor principal. Modifica este archivo para cambiar los elementos del menú lateral o el pie de página de la aplicación.
*   **login.html**: Vista de inicio de sesión con el modal de recuperar contraseña. Modifica este archivo para cambiar el diseño de la tarjeta de login o los campos requeridos.
*   **dashboard.html**: Panel de bienvenida. Contiene tarjetas de accesos directos ("Renovación de Cédula", "Pasaporte" y "Mi Información"). Modifica este archivo para habilitar nuevas secciones o cambiar textos descriptivos.
*   **renovacion.html**: Formulario de sólo lectura que muestra los datos del ciudadano que serán renovados. Permite editar el estilo de las cajas de datos, la firma y la huella digital mostrada.
*   **subir_foto.html**: Zona de carga interactiva con soporte para arrastrar archivos y lista visual de requisitos obligatorios. Puedes modificar el texto de los requisitos o el diseño del dropzone.
*   **exito.html**: Página de cierre con carnet digital de éxito generado con la nueva foto y el botón de descarga del PDF. Puedes modificar los estilos visuales de la simulación de cédula digital mostrada en el navegador.
*   **pasaporte.html**: Vista de mantenimiento. Puedes modificar el texto informativo o el botón de redirección.
