# Registro de Cambios — Correcciones de Funcionalidad (SIVA)

Este documento describe, de forma detallada y explicativa, las correcciones
funcionales aplicadas al proyecto SIVA tras la revisión de código. El foco fue
**la funcionalidad** (que las cosas funcionen y hagan lo que dice la
documentación), no la seguridad ni el despliegue.

> Resumen rápido: se corrigió el rechazo de fotos de mascotas (#1), se activó y
> **calibró** el reconocimiento facial real (#2), se eliminó un fallo por fecha
> en años bisiestos (#3), se documentó con precisión el redimensionado
> automático (#4), se limpiaron problemas menores, se hicieron **configurables
> por variables de entorno** los umbrales de similitud facial, tolerancia y fondo
> claro (con `.env.example`) y se ampliaron las pruebas de 4 a 23 casos.

---

## Índice

1. [#1 — Rechazo por nombre de mascota ahora funciona](#1)
2. [#2 — Reconocimiento facial real, activado y calibrado](#2)
3. [#3 — Fallo por fecha en años bisiestos](#3)
4. [#4 — Documentación real del redimensionado (relación de aspecto)](#4)
5. [Sobre #5, #6 y #7 (no aplicados y por qué)](#no-aplicados)
6. [Problemas menores corregidos](#menores)
7. [Umbrales configurables por entorno + .env.example](#fondo)
8. [Pruebas nuevas](#pruebas)
9. [Cómo instalar y verificar](#verificar)

---

<a name="1"></a>
## 1. #1 — El rechazo por nombre de mascota (`perro`/`dog`) ahora funciona

**Problema.** El `README` (sección "Pruebas del Trámite", paso 2) indica que para
simular un rechazo se debe subir un archivo cuyo nombre contenga `perro`, `dog`,
`mascota`, etc., y el sistema debería bajar la coincidencia a **35.5%** y
rechazar. En la práctica **nunca rechazaba**: la foto se aprobaba y llegaba a la
pantalla de éxito.

**Causa raíz.** En `routes.py`, el archivo subido se **renombra** a
`foto_nueva_<id>_<hash>.ext` *antes* de la comparación. El comparador
(`_comparar_por_histograma`) buscaba la palabra clave con
`os.path.basename(ruta_nueva)`, es decir, sobre el nombre YA renombrado, donde la
palabra `perro` ya no existe. El filtro nunca se activaba.

**Solución (opción A: usar el nombre original).**
- `routes.py`: se conserva `nombre_original = archivo.filename` antes de renombrar
  y se pasa a `comparar_rostros(..., nombre_original=nombre_original)`.
- `face_comparator.py`: `comparar_rostros` y `_comparar_por_histograma` aceptan un
  parámetro `nombre_original`. El filtro de mascotas usa
  `(nombre_original or os.path.basename(ruta_nueva))`.

**Archivos:** `app/routes.py`, `app/utils/face_comparator.py`.

**Verificación:** `tests/test_routes.py::test_rechazo_por_nombre_de_mascota` y
`tests/test_comparator.py::test_rechazo_por_nombre_mascota`. Al subir `perro.png`
la ruta ahora redirige a `/subir-foto` (rechazo) en lugar de `/exito`.

---

<a name="2"></a>
## 2. #2 — Reconocimiento facial real: activado y **calibrado**

**Problema.** El README promete comparación biométrica con redes neuronales
(`DeepFace` / `face_recognition`), pero esas librerías **no estaban declaradas en
`requirements.txt`** ni instaladas, por lo que el sistema siempre caía al
respaldo por histograma de color. La biometría "real" no ocurría nunca.

**Qué se hizo (opción A: instalar `face_recognition`).**
Se instaló y verificó la pila biométrica completa sobre Python 3.12:

- `dlib-bin` (wheel precompilado de dlib; evita compilar desde código fuente).
- `face_recognition` (instalado con `--no-deps` para que no arrastre `dlib` de
  código fuente).
- `face_recognition_models` desde GitHub (la versión de PyPI, 0.1.3, está
  **incompleta**: le falta el predictor de 5 puntos).
- `setuptools<80` (la librería de modelos usa `pkg_resources`, eliminado en
  setuptools 80+).

Todo esto quedó encapsulado en `requirements-biometria.txt` y en el objetivo
`make biometria`, para que sea reproducible e **opcional**.

**Bug crítico de calibración detectado y corregido.** Al activar
`face_recognition` surgió un problema real: `face_recognition` trabaja con
**distancias**, no con porcentajes. La conversión ingenua `(1 - distancia) * 100`
daba, para la MISMA persona, apenas ~55-65%, que quedaba **por debajo del umbral
del 85%** configurado. Es decir: con reconocimiento real activado, ¡rechazaba a
la persona correcta!

Se añadió `_distancia_a_similitud(distancia)` en `face_comparator.py`, que ancla
el límite de coincidencia de `face_recognition` (distancia 0.6) al umbral del 85%:

| Distancia | Significado                | Similitud calibrada |
|-----------|----------------------------|---------------------|
| 0.0       | Rostro idéntico            | 100%                |
| 0.35      | Misma persona (típico)     | ~91% (✔ aprueba)    |
| 0.6       | Límite de coincidencia     | 85% (= umbral)      |
| 0.84      | Persona distinta           | ~34% (✘ rechaza)    |
| 1.0       | Totalmente distintos       | 0%                  |

**Prueba con rostros reales** (imágenes de ejemplo de la librería, no incluidas
en el repositorio):
- Misma persona (dos fotos distintas): **91.4%**, `coincide = True`.
- Personas distintas: **34.0%**, `coincide = False`.

**Limitación conocida (de datos, no de código).** Los 10 usuarios de prueba usan
**avatares de silueta**, no rostros reales. `face_recognition` no puede extraer un
"encoding" de una silueta, por lo que para esos usuarios cae elegantemente al
respaldo por histograma. Para **demostrar** el reconocimiento real ante el
profesor, reemplace `static/fotos/V-XXXXXXXX.png` por una foto de rostro real y
suba otra foto de la misma persona.

**Archivos:** `app/utils/face_comparator.py`, `requirements-biometria.txt`,
`Makefile`, `README.md`.

**Verificación:** `tests/test_comparator.py::test_calibracion_distancia_a_similitud`
y `test_similitud_monotona_decreciente`.

---

<a name="3"></a>
## 3. #3 — Fallo por fecha en años bisiestos

**Problema.** El PDF y el QR calculan la fecha de vencimiento con
`fecha.replace(year=year + 10)`. Si el documento se genera un **29 de febrero** y
el año destino no es bisiesto, `replace` lanza `ValueError: day is out of range
for month`, lo que hacía fallar toda la ruta `/verificar-foto`.

**Solución.** Se añadió la función `sumar_anios(fecha, anios)` en
`qr_generator.py`, que captura el `ValueError` y ajusta al 28 de febrero. Se usa
en `qr_generator.py` y `pdf_generator.py`.

**Archivos:** `app/utils/qr_generator.py`, `app/utils/pdf_generator.py`.

**Verificación:** `tests/test_pdf.py::test_29_de_febrero_no_crashea` y
`test_anio_normal`.

---

<a name="4"></a>
## 4. #4 — Documentación real del redimensionado (relación de aspecto)

**Problema.** La interfaz y el README anunciaban "Dimensiones: 336px × 448px"
como un requisito, pero el validador **nunca rechaza** por tamaño: redimensiona
automáticamente cualquier imagen a 336×448.

**Decisión (según lo solicitado).** El redimensionado automático es el
comportamiento **preferido** y se mantiene. No se tocó la interfaz ni el frontend.
Solo se **documentó lo que realmente ocurre**:

- En `photo_validator.py` se actualizaron las descripciones (docstrings) del
  módulo y de `_verificar_dimensiones_cv2` para dejar claro que no se rechaza por
  tamaño y que lo relevante es la **relación de aspecto 3:4**.
- En el `README.md` se reemplazó el requisito de píxeles exactos por una
  descripción basada en la **relación de aspecto 3:4** (la foto se redimensiona
  automáticamente a 336×448).

**Archivos:** `app/utils/photo_validator.py`, `README.md`
(no se modificó `app/templates/subir_foto.html`).

---

<a name="no-aplicados"></a>
## 5. Sobre #5, #6 y #7 (no aplicados y por qué)

- **#5 (falsos positivos de "gorra" con cabello oscuro):** según lo indicado,
  solo debía corregirse **si no se podía activar #2**. Como #2 sí se activó
  (reconocimiento facial real, calibrado), **no se modificó #5**.
  *Riesgo residual:* si se sube una **foto real** (no un avatar) de una persona
  de cabello oscuro, el detector de gorra por brillo (`_detectar_gorra`, umbral de
  brillo < 45) podría marcarla erróneamente. Si en el futuro se demuestra con
  fotos reales, conviene revisitar este umbral.
- **#6 (bypass de validación para placeholders):** no se tocó, por indicación
  expresa. Es lo que permite que los avatares de silueta pasen la validación en la
  demo.
- **#7 (fuente `arial.ttf` ausente en Linux):** no se tocó, por indicación
  expresa. Los avatares generados por `init_db.py` usan una fuente por defecto más
  pequeña en Linux (solo afecta la estética de las iniciales).

---

<a name="menores"></a>
## 6. Problemas menores corregidos

- **Código muerto eliminado.** Se quitó el bloque `MockValidator` /
  `MockComparator` / `MockPDFGen` de `routes.py`: nunca se ejecutaba (los módulos
  reales siempre importan) y `MockPDFGen` incluso devolvía la ruta de un PDF
  inexistente. Ahora la importación es directa.
- **`os.path.exists(None)`.** Se protegió `comparar_rostros` para el caso de un
  usuario sin foto previa (`ruta_foto_anterior = None`), evitando un `TypeError`.
- **Tipo inconsistente de `similitud`.** En la ruta `/exito`, el valor por defecto
  pasó de la cadena `'90.0'` a un número (`0.0`), coherente con el valor numérico
  que se guarda en `/verificar-foto`.

*Pendiente menor no abordado (es frontend):* `exito.html` referencia
`img/default_avatar.png`, que no existe; solo afecta si un usuario no tuviera foto
(no ocurre con los usuarios sembrados).

---

<a name="fondo"></a>
## 7. Umbrales configurables por entorno + `.env.example`

**Contexto.** La comprobación de "fondo blanco" rechazaba cualquier foto cuyo
fondo tuviera menos del **70%** de píxeles claros (valor fijo en el código). Al
probar el reconocimiento facial con una foto real de fondo no blanco, la foto se
rechazaba **antes** de llegar a la comparación biométrica, con el mensaje
"El fondo no es lo suficientemente claro (obtenido 52.4% claro)" — cifra que se
puede confundir con un porcentaje de similitud facial (no lo es).

**Solución.** El umbral pasó a ser **configurable**:
- `config.py`: nueva opción `FONDO_THRESHOLD` (por defecto `70.0`), leída también
  desde la variable de entorno `FONDO_THRESHOLD`.
- `photo_validator.py`: `validar_foto(ruta, umbral_fondo=70.0)` usa el umbral
  recibido en lugar del valor fijo. Con `0` se desactiva de hecho la exigencia.
- `routes.py`: pasa `current_app.config['FONDO_THRESHOLD']` a `validar_foto`.

**Para probar con fotos de fondo no blanco**, baje el umbral sin tocar el código:

```bash
FONDO_THRESHOLD=0 python run.py      # o edite su archivo .env
```

### Umbral y tolerancia faciales configurables

También se hicieron configurables por entorno:
- `FACIAL_THRESHOLD` (config.py, por defecto `0.85`): umbral de similitud para aceptar.
- `FACIAL_TOLERANCE` (config.py, por defecto `0.6`): tolerancia de distancia de
  `face_recognition`. Se pasa por `comparar_rostros(..., umbral=, tolerancia=)`
  hasta `_distancia_a_similitud`.

Como la calibración **ancla** la tolerancia al umbral (en `distancia == tolerancia`
la similitud vale exactamente el umbral%), la decisión de aceptar/rechazar depende
en la práctica de **`FACIAL_TOLERANCE`** (se acepta si `distancia <= tolerancia`);
`FACIAL_THRESHOLD` afecta sobre todo el porcentaje mostrado.

**Valores tuneados para la demo (solo en `.env` / `.env.example`).** Para el perfil
de `V-12345678` se ajustó `FACIAL_TOLERANCE=0.3` (y `FONDO_THRESHOLD=50` para que las
fotos de fondo ~52% pasen la validación), de modo que:

| Imagen subida | Distancia | Resultado |
|---|---|---|
| `foto_nueva_9_cfa8f672.png` | 0.000 | **PASA** (100%) |
| `foto_nueva_9_57015a8a.jpg` | 0.375 | RECHAZA (75.8%) |
| `foto_nueva_9_2140a524.jpg` | 0.417 | RECHAZA (70.8%) |

Para uso general, suba `FACIAL_TOLERANCE` a `0.6` (recomendado por face_recognition).

**`.env.example` (nuevo).** Se añadió una plantilla de variables de entorno
(`SECRET_KEY`, `UPLOAD_FOLDER`, `FACIAL_THRESHOLD`, `FACIAL_TOLERANCE`,
`FONDO_THRESHOLD`). Cópiela a `.env`:

```bash
cp .env.example .env
```

**Archivos:** `config.py`, `app/utils/photo_validator.py`,
`app/utils/face_comparator.py`, `app/routes.py`, `.env` y `.env.example`,
`README.md`.

**Verificación:** `tests/test_validator.py::TestUmbralFondoConfigurable` (misma
foto rechazada con umbral 70, aceptada con 40), `TestConfigDesdeEntorno` (las tres
variables se leen del entorno) y `tests/test_comparator.py::test_calibracion_parametrizable`.

---

<a name="pruebas"></a>
## 8. Pruebas nuevas (de 4 a 20 casos)

Se pasó de pruebas puramente estructurales ("el diccionario tiene tales claves")
a pruebas que verifican **decisiones reales** de aceptación/rechazo:

- `tests/test_routes.py` (nuevo, integración con el cliente de Flask):
  - login correcto e incorrecto,
  - flujo exitoso completo → genera y descarga un PDF válido,
  - **rechazo por nombre `perro.png`** (cubre #1),
  - rechazo de foto sin rostro,
  - bloqueo tras 3 intentos fallidos.
- `tests/test_pdf.py` (nuevo): `sumar_anios` en años bisiestos (cubre #3) y
  generación de un PDF válido (cabecera `%PDF`).
- `tests/test_comparator.py` (ampliado): calibración de la distancia (cubre #2),
  monotonía, rechazo por nombre de mascota (cubre #1) y guardia contra `None`.
- `tests/test_validator.py` (ampliado): umbral de fondo claro configurable
  (misma foto rechazada con 70 y aceptada con 40) y lectura de las tres variables
  de entorno en subproceso (`TestConfigDesdeEntorno`; cubre la sección 7).

Ejecutar con `make test` o `python -m unittest discover -s tests -v`.
Resultado: **23 pruebas, todas OK**. Las pruebas funcionan **con o sin** la
biometría instalada (usan el respaldo cuando corresponde) y son deterministas
(no dependen de archivos que el usuario pueda haber reemplazado ni de valores del
`.env`; la configurabilidad por entorno se prueba en un subproceso).

---

<a name="verificar"></a>
## 9. Cómo instalar y verificar

```bash
# Entorno + dependencias base (usa Python 3.12; ver nota más abajo)
make install

# (Opcional) Activar reconocimiento facial REAL
make biometria

# Sembrar base de datos y usuarios de prueba
make seed

# Ejecutar pruebas
make test

# Levantar el servidor
make run     # http://127.0.0.1:5000
```

> **Nota sobre Python:** las librerías fijadas (Pillow/OpenCV) tienen "wheels"
> para **Python 3.12/3.13**, no para 3.14. El `Makefile` usa `python3.12` por
> defecto (`make install PYTHON=python3.13` para cambiarlo).

### Archivos modificados / creados

| Archivo | Cambio |
|---|---|
| `config.py` | `FONDO_THRESHOLD`, `FACIAL_THRESHOLD` y `FACIAL_TOLERANCE` configurables por entorno (sección 7) |
| `app/routes.py` | Nombre original al comparador (#1); código muerto; `similitud`; pasa `FONDO_THRESHOLD` |
| `app/utils/face_comparator.py` | Calibración `_distancia_a_similitud` (#2); `umbral`/`tolerancia` configurables (sección 7); `nombre_original` (#1); guardia `None` |
| `app/utils/qr_generator.py` | `sumar_anios` (#3) |
| `app/utils/pdf_generator.py` | Uso de `sumar_anios` (#3) |
| `app/utils/photo_validator.py` | Docstrings del redimensionado (#4); `umbral_fondo` configurable (sección 7) |
| `README.md` | Relación de aspecto 3:4 (#4); redacción de biometría (#2); notas de Makefile |
| `.env.example` | Nuevo: plantilla de variables de entorno; valores de demo tuneados (sección 7) |
| `.env` | Valores tuneados para la demo de V-12345678 (no versionado) |
| `requirements-biometria.txt` | Nuevo: pila biométrica opcional (#2) |
| `Makefile` | Nuevo objetivo `biometria` (#2) |
| `tests/test_routes.py` | Nuevo: pruebas de integración (deterministas) |
| `tests/test_pdf.py` | Nuevo: PDF y años bisiestos |
| `tests/test_comparator.py` | Ampliado: calibración y rechazos |
| `tests/test_validator.py` | Ampliado: umbral de fondo configurable |
