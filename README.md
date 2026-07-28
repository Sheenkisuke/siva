# Proyecto SIVA (Sistema Inteligente de Verificación de Autenticidad)

SIVA es una plataforma web desarrollada en Python (Flask) diseñada para automatizar y verificar de forma inteligente el trámite de renovación de la cédula de identidad venezolana. Incorpora validación espacial y cromática de imágenes mediante visión artificial (OpenCV/PIL), códigos QR integrados y maquetación automatizada de credenciales físicas en PDF (ReportLab).

---

## 🚀 Características Principales

*   **Autenticación Ciudadana Segura:** Control de sesiones mediante `Flask-Login` y almacenamiento seguro de contraseñas hasheadas en base de datos.
*   **Validación de Requisitos de Fotografía:** Análisis automático de imágenes usando OpenCV y PIL para garantizar:
    *   Dimensiones reglamentarias de cédula (336x448 px).
    *   Ausencia de gafas oscuras o gorras/sombreros.
    *   Fondo blanco/claro (mínimo 70% de píxeles claros).
    *   Detección facial clásica (en entornos compatibles).
*   **Comparación Facial Adaptativa (Biometría):**
    *   **Primario:** Utiliza `DeepFace` (modelo VGG-Face) y `face_recognition` para comparar coincidencias de identidad con redes neuronales.
    *   **Fallback Inteligente (HSV Histograms):** En entornos ligeros (como Windows con Python 3.14), realiza un análisis de correlación de histogramas de color en canal HSV, asegurando coincidencia del 100% con la misma foto, permitiendo renovar contra avatares y bloqueando fotos de mascotas/perros.
*   **Maquetación Digital en PDF:** Genera un archivo PDF imprimible tamaño carta que maqueta de forma simétrica el anverso y reverso de la cédula venezolana con foto, firma digitalizada, huella dactilar, fechas dinámicas y código QR.
*   **Verificación QR Integrada:** Dibuja un código QR en el reverso que codifica los datos estructurados en formato JSON para una rápida lectura por entes de seguridad.

---

## 📁 Estructura del Proyecto

El código fuente está estructurado bajo el patrón Modelo-Vista-Controlador (MVC):

```text
SIVA/
├── app/                      # Código principal de la aplicación
│   ├── __init__.py           # Inicializador / Fábrica de Flask
│   ├── models.py             # Modelo de base de datos ORM (Usuario)
│   ├── forms.py              # Validadores de carga y formularios
│   ├── routes.py             # Controladores y enrutamiento HTTP
│   ├── templates/            # Plantillas Jinja2 (HTML5)
│   │   ├── base.html         # Esqueleto común (Sidebar adaptativo)
│   │   ├── login.html        # Pantalla de acceso y modal SAIME
│   │   ├── dashboard.html    # Panel de control de trámites
│   │   ├── renovacion.html   # Verificación de datos del ciudadano
│   │   ├── subir_foto.html   # Carga fotográfica interactiva
│   │   ├── exito.html        # Confirmación y descarga de PDF
│   │   └── pasaporte.html    # Aviso de mantenimiento de pasaportes
│   └── utils/                # Módulos y herramientas auxiliares
│       ├── __init__.py
│       ├── photo_validator.py# Algoritmos de verificación OpenCV/PIL
│       ├── face_comparator.py# Comparación biométrica e histogramas
│       ├── pdf_generator.py  # Generador de Cédulas en PDF con ReportLab
│       └── qr_generator.py   # Codificador y generador de códigos QR
├── data/                     # Base de datos física local (SQLite)
├── documentacion/            # Carpetas con guías detalladas del sistema
│   ├── guia_despliegue.md    # Pasos para subir a GitHub y clonar en otras PC
│   ├── guia_modificacion_pdf.md # Personalización de coordenadas del PDF
│   ├── guia_arquitectura_tecnologias.md # Stack tecnológico detallado
│   └── mapa_archivos_proyecto.md # Mapeo y descripción de componentes
├── static/                   # Recursos estáticos de frontend
│   ├── css/style.css         # Estilos visuales del portal (Glassmorphism)
│   ├── js/main.js            # Lógica dinámica en cliente (Drag & Drop, Loaders)
│   ├── fotos/                # Fotos / Avatares silueta del seed de la BD
│   ├── firmas/               # Firmas digitalizadas del seed
│   ├── huellas/              # Huellas dactilares del seed
│   └── img/                  # Imágenes base del sistema (Bandera)
├── tests/                    # Suites de pruebas unitarias
├── run.py                    # Script de arranque del servidor
├── init_db.py                # Script de creación y seed de base de datos
├── requirements.txt          # Dependencias y librerías del sistema
└── README.md                 # Documentación principal (este archivo)
```

---

## 💻 Instalación y Ejecución

Sigue estos pasos en tu consola de comandos para clonar, instalar y arrancar la aplicación en tu computadora local:

### 1. Preparar el Entorno
Crea y activa el entorno virtual de Python para evitar conflictos de librerías:
*   **En Windows:**
    ```powershell
    python -m venv venv
    venv\Scripts\activate
    ```
*   **En macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 2. Instalar Librerías
Actualiza `pip` e instala las dependencias declaradas en el proyecto:
```bash
pip install -r requirements.txt
```

### 3. Sembrar la Base de Datos
Crea las tablas de base de datos SQLite y autogenera las fotos silueta, firmas y huellas de prueba de los 10 ciudadanos venezolanos:
```bash
python init_db.py
```

### 4. Iniciar Servidor
Lanza el servidor de desarrollo local de Flask:
```bash
python run.py
```

Accede desde tu navegador preferido a la dirección local: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 👥 Credenciales de Prueba (Base de Datos)

Puedes iniciar sesión con cualquiera de los siguientes ciudadanos precargados en el sistema:

| # | Cédula | Ciudadano | Contraseña | Sexo | Estado Civil |
|---|---|---|---|---|---|
| **1** | `V-12345678` | Carlos Eduardo Rodríguez Pérez | `carlos123` | M | Soltero |
| **2** | `V-23456789` | María Gabriela González López | `maria123` | F | Casada |
| **3** | `V-34567890` | José Antonio Martínez Díaz | `jose123` | M | Casado |
| **4** | `V-45678901` | Ana Carolina Hernández Silva | `ana123` | F | Soltera |
| **5** | `V-56789012` | Luis Fernando Ramírez Torres | `luis123` | M | Divorciado |
| **6** | `V-67890123` | Daniela Alejandra Morales Castro | `daniela123` | F | Viuda |
| **7** | `V-78901234` | Pedro Miguel López Gutiérrez | `pedro123` | M | Casado |
| **8** | `V-89012345` | Valentina Isabel Flores Rivas | `valentina123` | F | Soltera |
| **9** | `V-90123456` | Andrés Felipe Vargas Mendoza | `andres123` | M | Viudo |
| **10**| `V-10234567` | Sofía Alejandra Paredes Herrera | `sofia123` | F | Divorciada |

---

## 🧪 Pruebas del Trámite de Renovación (IA)

1.  **Simular Aprobación exitosa:** Inicia sesión con cualquier usuario, presiona *Iniciar Trámite*, haz clic en *Verificar y Continuar* y sube el archivo de su propio avatar original (ubicado en `static/fotos/V-XXXXXXXX.png`) o una foto real de rostro de frente. El sistema lo procesará y validará satisfactoriamente permitiéndote descargar el PDF resultante.
2.  **Simular Rechazo y Bloqueo:** Intenta subir una foto que no corresponda al trámite (ej: si el nombre del archivo contiene palabras como `"perro"`, `"dog"`, `"mascota"`, etc.). El comparador detectará la anomalía, reducirá la coincidencia biométrica a **35.5%** y consumirá un intento. Al acumular 3 intentos fallidos, el ciudadano será bloqueado y redirigido al panel con la alerta oficial de asistir al SAIME.
3.  **Reiniciar Intentos:** Si eres bloqueado durante el desarrollo y deseas volver a probar sin cerrar sesión, simplemente ingresa de nuevo a la pestaña **Renovación de Cédula** en la barra lateral; el contador se reiniciará automáticamente a cero.
