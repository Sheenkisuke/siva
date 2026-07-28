# Proyecto SIVA (Sistema Inteligente de Verificación de Autenticidad)

SIVA es una plataforma web desarrollada en Python (Flask) diseñada para automatizar y verificar de forma inteligente el trámite de renovación de la cédula de identidad venezolana. Incorpora validación espacial y cromática de imágenes mediante visión artificial (OpenCV/PIL), códigos QR integrados y maquetación automatizada de credenciales físicas en PDF (ReportLab).

---

## 🚀 Características Principales

*   **Autenticación Ciudadana Segura:** Control de sesiones mediante `Flask-Login` y almacenamiento seguro de contraseñas hasheadas en base de datos.
*   **Validación de Requisitos de Fotografía:** Análisis automático de imágenes usando OpenCV y PIL para garantizar:
    *   Relación de aspecto 3:4 de la cédula: la foto se **redimensiona automáticamente** a 336x448 px, por lo que no se exige un tamaño exacto en píxeles (el requisito real es la proporción/relación de aspecto, no la resolución).
    *   Ausencia de gafas oscuras o gorras/sombreros.
    *   Fondo blanco/claro (mínimo de píxeles claros **configurable**; 70% por defecto vía `FONDO_THRESHOLD`, ver `.env.example`).
    *   Detección facial clásica (en entornos compatibles).
*   **Comparación Facial Adaptativa (Biometría):**
    *   **Reconocimiento facial real (opcional):** Con `face_recognition` (dlib) instalado mediante `make biometria`, compara identidades con redes neuronales. La distancia facial se **calibra** para que una coincidencia real supere el umbral y una persona distinta quede por debajo. El umbral y la tolerancia son **configurables** (`FACIAL_THRESHOLD` / `FACIAL_TOLERANCE`, ver `.env.example`).
    *   **Respaldo por histograma (por defecto):** Si no se instala la biometría, realiza una correlación de histogramas de color HSV; asegura ~100% con la misma imagen, permite renovar contra los avatares de demostración y **rechaza** archivos cuyo nombre indique mascota/animal (p. ej. `perro`, `dog`).
    *   **Nota:** los usuarios de prueba usan avatares de silueta (no rostros reales), por lo que el reconocimiento facial real se demuestra mejor sustituyendo `static/fotos/V-XXXXXXXX.png` por una foto de rostro real. Ver `documentacion/registro_de_cambios.md`.
*   **Maquetación Digital en PDF:** Genera un archivo PDF imprimible tamaño carta con el anverso y el reverso de la cédula venezolana. El anverso reproduce la maquetación real —banda tricolor con el encabezado, número de cédula agrupado en miles, apellidos y nombres, firma y huella a la izquierda, las cuatro casillas de fechas y estado civil, la nacionalidad y la fotografía a la derecha—; todas las posiciones se expresan como fracciones del tamaño de la tarjeta, así que cambiar `ANCHO_TARJETA` reescala el diseño completo. El reverso lleva el código QR.
*   **Vista Previa Fiel al PDF:** La pantalla de éxito muestra el anverso y el reverso en SVG, dibujados con la **misma maquetación** que el PDF (`pdf_generator.vista_previa` recorre la misma especificación de campos que el generador), así que la vista previa no es una maqueta aparte y no puede desviarse del documento que se descarga.
*   **Verificación QR Integrada:** Dibuja un código QR en el reverso que codifica los datos estructurados en formato JSON para una rápida lectura por entes de seguridad.
*   **Selector de Huellas por Dedo:** En *Renovación de Cédula*, el apartado "Huella Digital" muestra las dos manos con los **10 dedos seleccionables**. Al pulsar un dedo se muestra su huella ampliada con el nombre del dedo, y con "‹ Volver" (o `Escape`) se regresa para elegir otro. `init_db.py` genera una huella distinta por dedo (`static/huellas/V-XXXXXXXX_1.png` … `_10.png`). **El dedo elegido queda marcado y es el que se estampa en el PDF**; si no se elige ninguno se usa la huella principal (`V-XXXXXXXX.png`).

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
│   ├── huellas/              # Huellas del seed: la principal (PDF) y una por dedo (_1.._10)
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

> **Atajo con Makefile (Linux/macOS):** `make install` crea el entorno virtual e instala todo; `make seed` siembra la base de datos; `make run` arranca el servidor; `make test` ejecuta las pruebas. Ver `make help`.
>
> **Reconocimiento facial real (opcional):** para activar la biometría real con `face_recognition`/dlib ejecuta `make biometria` (o `pip install --no-deps -r requirements-biometria.txt`). Sin esto, el sistema usa el respaldo por histograma de color.

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
