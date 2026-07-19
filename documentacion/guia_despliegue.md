# Guía de Despliegue y Ejecución del Proyecto SIVA

Esta guía explica paso a paso cómo subir el proyecto a un repositorio de GitHub, clonarlo y ejecutarlo en cualquier otra computadora.

---

## 📋 Requisitos Previos

Para ejecutar este proyecto en otra computadora, es necesario tener instalado:

1. **Python 3.10 o superior** (Se recomienda Python 3.11 o 3.12 para máxima compatibilidad con OpenCV; en Python 3.14 funciona con la validación básica automatizada).
2. **Git** (Para clonar el repositorio).
3. Un navegador web moderno (Chrome, Edge, Firefox, Brave).

---

## 📦 1. Cómo Subir el Proyecto a GitHub (Paso a Paso)

Si deseas crear tu propio repositorio en GitHub para el proyecto, sigue estos pasos desde la terminal de la computadora actual:

### Paso 1: Inicializar Git en la carpeta del proyecto
Abre una terminal en `C:\Users\User1\.gemini\antigravity\scratch\SIVA` y ejecuta:
```bash
git init
```

### Paso 2: Crear el archivo `.gitignore`
Es fundamental no subir archivos temporales, el entorno virtual o bases de datos locales. Crea un archivo llamado `.gitignore` en la raíz del proyecto con el siguiente contenido:
```text
# Entorno virtual
venv/
.venv/
env/

# Base de datos SQLite local
data/database.db
instance/

# Archivos de subida temporales de prueba
static/uploads/*
!static/uploads/.gitkeep

# Caché de Python
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/

# Variables de entorno secretas
.env

# Archivos temporales de ReportLab o PDFs generados fuera de static/uploads
*.pdf
```

### Paso 3: Añadir los archivos y hacer el primer commit
```bash
git add .
git commit -m "Initial commit: Proyecto SIVA funcional"
```

### Paso 4: Crear el repositorio en GitHub
1. Entra a tu cuenta en [GitHub](https://github.com).
2. Haz clic en **New repository**.
3. Nómbralo (ej: `siva-saime`) y manténlo como Público o Privado.
4. **No** selecciones "Add a README", "Add .gitignore" o "Choose a license" (ya que los tenemos en local).
5. Haz clic en **Create repository**.

### Paso 5: Vincular el repositorio local con GitHub y subirlo
GitHub te mostrará unas líneas de comando similares a estas. Ejecútalas en tu terminal:
```bash
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```

---

## 💻 2. Cómo Ejecutar SIVA en otra Computadora

Cuando tú o cualquier otra persona obtenga el proyecto a través de Git, estos son los pasos exactos para ponerlo en marcha desde cero:

### Paso 1: Clonar el repositorio
Abre la terminal en la carpeta donde deseas guardar el proyecto y ejecuta:
```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git SIVA
cd SIVA
```

### Paso 2: Crear el entorno virtual de Python
El entorno virtual aísla las librerías del proyecto para que no entren en conflicto con el sistema:
- **En Windows:**
  ```powershell
  python -m venv venv
  ```
- **En macOS o Linux:**
  ```bash
  python3 -m venv venv
  ```

### Paso 3: Activar el entorno virtual
- **En Windows (PowerShell):**
  ```powershell
  venv\Scripts\Activate.ps1
  ```
- **En Windows (CMD):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **En macOS o Linux:**
  ```bash
  source venv/bin/activate
  ```

### Paso 4: Instalar las dependencias del proyecto
Con el entorno virtual activado, instala todas las librerías necesarias con un solo comando:
```bash
pip install -r requirements.txt
```

### Paso 5: Inicializar la Base de Datos y Generar Assets
Antes de arrancar el servidor por primera vez, debes crear las tablas de la base de datos SQLite y generar las firmas, huellas y fotos silueta de prueba de los 10 ciudadanos venezolanos:
```bash
python init_db.py
```
*(Este script creará la carpeta `data/database.db` y llenará las carpetas en `static/` con las imágenes de prueba).*

### Paso 6: Ejecutar la aplicación
Para iniciar el servidor de desarrollo local:
```bash
python run.py
```

### Paso 7: Acceder a la web
Abre tu navegador e ingresa a:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔑 3. Credenciales de Prueba disponibles

Puedes iniciar sesión con cualquiera de las siguientes identidades pre-cargadas:

| Cédula | Nombres | Apellidos | Contraseña |
|---|---|---|---|
| **V-12345678** | Carlos Eduardo | Rodríguez Pérez | `carlos123` |
| **V-23456789** | María Gabriela | González López | `maria123` |
| **V-34567890** | José Antonio | Martínez Díaz | `jose123` |
| **V-45678901** | Ana Carolina | Hernández Silva | `ana123` |
| **V-56789012** | Luis Fernando | Ramírez Torres | `luis123` |
| **V-67890123** | Daniela Alejandra | Morales Castro | `daniela123` |
| **V-78901234** | Pedro Miguel | López Gutiérrez | `pedro123` |
| **V-89012345** | Valentina Isabel | Flores Rivas | `valentina123` |
| **V-90123456** | Andrés Felipe | Vargas Mendoza | `andres123` |
| **V-10234567** | Sofía Alejandra | Paredes Herrera | `sofia123` |
