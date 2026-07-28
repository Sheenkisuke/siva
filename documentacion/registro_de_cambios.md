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
> Después se agregó el **selector de huellas por dedo** (sección 10) y se
> **rediseñó el anverso del PDF** según la cédula real, estampando la huella del
> dedo elegido (sección 11), y la **vista previa de /exito pasó a derivarse de la
> misma maquetación** del PDF (sección 12); la suite quedó en 49 casos.

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
10. [Nueva funcionalidad — Selector de huellas por dedo](#huellas)
11. [Rediseño del anverso del PDF según la cédula real](#anverso)
12. [La vista previa de /exito, calcada del PDF](#previa)

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
## 8. Pruebas nuevas (de 4 a 23 casos)

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
| `init_db.py` | Huella por dedo y semilla estable (sección 10) |
| `app/templates/renovacion.html` | Selector de huellas de dos vistas (sección 10) |
| `static/js/main.js` | Intercambio de vistas del selector (sección 10) |
| `static/css/style.css` | Estilos del selector y de los puntos (sección 10) |
| `static/img/manos.png` | Nuevo: imagen base de las dos manos (sección 10) |

---

<a name="huellas"></a>
## 10. Nueva funcionalidad — Selector de huellas por dedo

**Pedido.** En la misma vista donde se mostraba una sola huella, poder ver las
diez: una imagen de las dos manos con los 10 dedos seleccionables y, al pulsar un
dedo, su huella, con la opción de volver y elegir otro.

**Qué se hizo.**

- `init_db.py` genera por ciudadano la huella principal (`<cedula>.png`, la que
  estampa el PDF) **más una por dedo** (`<cedula>_1.png` … `<cedula>_10.png`):
  110 archivos para los 10 ciudadanos sembrados. El patrón varía el núcleo, la
  excentricidad, la separación de anillos y la inclinación. Variar solo el número
  de anillos **no alcanzaba**: las diez huellas salían casi idénticas y el
  selector perdía sentido.
- El dibujo usa una semilla derivada de `(cédula, dedo)` en vez del `random`
  global. Las huellas se versionan en el repositorio: sin semilla estable, cada
  `make seed` producía 110 archivos distintos y ensuciaba el historial.
- `app/routes.py` declara `DEDOS`: número de archivo, nombre del dedo y
  coordenadas `x`/`y` **en porcentaje** del ancho y alto de
  `static/img/manos.png`.
- `renovacion.html` reemplaza la miniatura única de "Huella Digital" por dos
  vistas: las manos con 10 botones, y el detalle del dedo elegido (huella grande,
  nombre y "‹ Volver").
- `static/js/main.js` intercambia las vistas con la clase `detalle-activa` (mismo
  patrón `.active` que usan el sidebar y el modal del login). `Escape` también
  regresa al selector.

**Detalle importante de posicionamiento.** Los puntos se ubican en
**porcentajes** y se centran con `translate(-50%, -50%)`, así el centro del punto
cae sobre la yema a cualquier ancho de render. Su contenedor **no debe llevar
`padding`**: los porcentajes de un elemento absoluto se resuelven contra la *caja
de relleno* del contenedor, de modo que reutilizar `.doc-img-wrapper` (que tiene
`padding: 10px`) corría los puntos hasta ~9 px en los dedos de los extremos. Por
eso `.huellas-manos` es una clase propia y sin relleno.

**Alcance.** Es solo de consulta: elegir un dedo **no cambia** la huella que
estampa el PDF, que sigue siendo `Usuario.huella_ruta`. Cambiarlo exigiría
persistir la selección.

**Los diez dedos.** Los dedos 5 y 6 son los pulgares, que en la imagen se tocan
en el centro:

| # | Dedo | # | Dedo |
|---|---|---|---|
| 1 | Meñique izquierdo | 6 | Pulgar derecho |
| 2 | Anular izquierdo | 7 | Índice derecho |
| 3 | Medio izquierdo | 8 | Medio derecho |
| 4 | Índice izquierdo | 9 | Anular derecho |
| 5 | Pulgar izquierdo | 10 | Meñique derecho |

**Pruebas añadidas** (en `tests/test_routes.py`, suite de 23 → **31 casos**):
`TestSelectorHuellas` comprueba que se dibujen los 10 puntos, que cada uno
apunte a la huella de su dedo, que las coordenadas vayan en porcentaje y que
`/renovacion` siga exigiendo sesión; `TestGeneracionDeHuellas` comprueba que se
generen 11 archivos por ciudadano, que los 10 dedos tengan patrones distintos y
que regenerar produzca archivos idénticos.

---

<a name="anverso"></a>
## 11. Rediseño del anverso del PDF según la cédula real

**Pedido.** Que el PDF se pareciera a una cédula real —diseño y posición de las
imágenes— y que estampara **la huella del dedo elegido en la interfaz**.

### La huella elegida llega al PDF

Antes el selector era solo de consulta. Ahora la elección viaja así:

1. En `/renovacion`, al elegir un dedo el JS marca el punto y añade `?dedo=N` al
   enlace de "Verificar y Continuar".
2. `subir_foto()` lee ese parámetro y lo guarda en `session['dedo_huella']`,
   validándolo contra `DEDOS` (un valor fuera de rango o no numérico se ignora).
3. `verificar_foto()` arma la ruta `huellas/<cedula>_<N>.png` y se la pasa a
   `generar_pdf(..., ruta_huella=...)`.
4. Si no se eligió dedo, o el archivo no existe, se usa `Usuario.huella_ruta`
   como siempre: el comportamiento anterior queda intacto.

El dedo elegido queda marcado en amarillo sobre las manos y rotulado ("Huella que
se estampará en la cédula: Índice derecho"), y **sobrevive a la recarga** porque
se relee de la sesión al volver a `/renovacion`.

### Maquetación medida, no estimada

Las posiciones se **midieron sobre la imagen de referencia** (1080x764 px) con un
script: recuadros de cada elemento y altura de mayúscula de cada texto. En
`pdf_generator.py` todo se expresa como **fracciones** del ancho y del alto de la
tarjeta, contando la vertical desde arriba (como se lee la imagen); `_fy()` las
traduce al sistema de ReportLab, que mide desde abajo. Cambiar el tamaño de la
tarjeta es tocar solo `ANCHO_TARJETA`.

Elementos del anverso: banda tricolor redondeada con "REPUBLICA BOLIVARIANA DE
VENEZUELA" y "CEDULA DE IDENTIDAD" en letras separadas, número de cédula
agrupado en miles (`V   12.345.678`), número de oficina, rúbrica y cargo del
director, apellidos y nombres con sus etiquetas, firma y huella del titular a la
izquierda, las cuatro casillas (F. NACIMIENTO / EDO.CIVIL / F.EXPEDICION /
F.VENCIMIENTO, esta última solo mes/año como en el original), la nacionalidad y
la fotografía a la derecha.

### Tres detalles que costaron

- **Tipografía condensada.** La cédula real está impresa con una condensada. Con
  Helvetica, respetar la altura de mayúscula medida deja los textos demasiado
  anchos (se montaban unos sobre otros), y bajar el cuerpo para que quepan los
  deja mucho más bajos que en el original. La salida fue comprimir en horizontal
  con `Tz` (`_texto_condensado`), que es justo lo que hace una condensada: se
  conservan a la vez la altura y el ancho de cada dato. Sirve además para los
  datos reales, que no miden lo mismo que los de la imagen ('RODRÍGUEZ PÉREZ' es
  más largo que 'ARONICO TORRES').
- **El estado gráfico del PDF persiste.** `charSpace` (`Tc`) y la escala
  horizontal (`Tz`) forman parte del estado gráfico y **no se reinician** al
  cerrar el bloque de texto: la separación del encabezado se filtró a toda la
  tarjeta y salió con las letras desparramadas. Ambos helpers van envueltos en
  `saveState`/`restoreState`. (Además `charSpace` está en el objeto de texto, no
  en el canvas: `canvas.setCharSpace` no existe.)
- **Imágenes sin deformar.** Foto, firma y huella se dibujan con
  `preserveAspectRatio=True, anchor='c'`: las proporciones de los archivos no
  coinciden con las de sus casillas y estirarlas se notaba.

### Lo que no se reprodujo

- **El escudo de armas de marca de agua** del centro: es un elemento de
  seguridad del documento y no se incluyó. Si se quiere, basta añadir el archivo
  y dibujarlo con transparencia antes del resto.
- **El nombre y la firma del director** son de maqueta: `DIRECTOR_NOMBRE` es un
  nombre inventado y la rúbrica es un trazo genérico dibujado con curvas, no la
  firma de ninguna persona.
- La tarjeta queda en **8,6 x 6,08 cm**, algo más alta que una ID-1 real
  (85,6 x 54 mm), porque se respetó la proporción de la foto de referencia para
  que la maquetación no saliera estirada. Para volver a la proporción real basta
  poner `PROPORCION_TARJETA = 85.6 / 54`.
- Las huellas se dibujan ahora con trazo **oscuro y más grueso**: con el gris
  claro anterior, impresas a ~1,5 cm de alto, quedaban casi en blanco.

**Pruebas** (suite de 31 → **42 casos**). En `tests/test_pdf.py`:
`TestFormatoDeDatosDelCarnet` cubre el agrupado en miles, la nacionalidad según
prefijo y la estabilidad del número de oficina; `TestHuellaEstampadaEnElPDF`
comprueba que la huella elegida se **incrusta de verdad** (una huella plana y una
ruidosa comprimen muy distinto, así que se compara el peso del PDF: comparar los
bytes enteros no serviría, porque ReportLab nombra los XObject con un hash de la
ruta y dos archivos distintos darían PDFs distintos aunque no se dibujara
ninguno) y que una ruta inexistente cae en la huella principal sin romper nada.
En `tests/test_routes.py` se añadió que `?dedo=N` se guarde en la sesión, que un
valor inválido se ignore y que el generador reciba la ruta del dedo elegido.

Verificación extra hecha a mano: se recorrió el trámite completo eligiendo el
dedo 7, se descargó el PDF, se rasterizó y se comparó el recorte de la huella
contra las diez candidatas. Correlación **0,857 con el dedo 7** y ≤0,15 con
todas las demás.

---

<a name="previa"></a>
## 12. La vista previa de /exito, calcada del PDF

**Problema.** La "Preview de cédula simplificada" de `exito.html` era una maqueta
HTML aparte, sin relación con el PDF: encabezado en degradado, sin huella ni
firma, sin número de oficina ni director, la cédula sin agrupar en miles, el
estado civil reducido a su inicial y sin fechas de expedición/vencimiento ni
nacionalidad. El ciudadano veía una cosa y descargaba otra.

**Enfoque.** No se rehízo la maqueta a mano: eso solo habría movido el problema a
"mantener dos diseños sincronizados". La vista previa pasó a **derivarse de la
misma maquetación que el PDF**:

- `_especificacion_anverso()` es ahora la **única** definición de los textos del
  anverso (qué dice cada uno, dónde va, con qué cuerpo, cuánto ocupa y cómo se
  alinea). La recorre el PDF para dibujar y la recorre la vista previa para armar
  el SVG. `_dibujar_anverso()` quedó bastante más corto al pasar a recorrerla.
- `datos_anverso()` centraliza los textos formateados (cédula agrupada en miles,
  número de oficina, fechas, nacionalidad), así que ninguna de las dos salidas
  puede mostrar un dato distinto de la otra.
- `TEXTOS_REVERSO`, las curvas de la rúbrica, los grosores de línea y las cajas
  de las imágenes también se comparten.
- `vista_previa()` devuelve ese modelo en unidades de un viewBox de
  `VB_ANCHO x VB_ALTO`, y `exito.html` lo emite como **SVG**.

**Por qué SVG y no divs.** Porque la correspondencia con el PDF es directa:

| PDF (ReportLab) | Vista previa (SVG) |
|---|---|
| fracciones del tamaño de la tarjeta | mismo número, sobre el viewBox |
| `charSpace` (`Tc`) del encabezado | `textLength` + `lengthAdjust="spacing"` |
| escala horizontal (`Tz`) al condensar | `textLength` + `lengthAdjust="spacingAndGlyphs"` |
| `preserveAspectRatio=True, anchor='c'` | `preserveAspectRatio="xMidYMid meet"` |
| Helvetica | `Helvetica, Arial` (métricamente compatible) |

El ancho natural de cada texto se mide con las métricas de Helvetica de
ReportLab —las mismas del PDF—, así que se condensa exactamente en los mismos
casos. Y como el SVG trae viewBox, escala solo: basta darle el ancho por CSS.

**El detalle que sí estaba mal.** SVG **colapsa los espacios múltiples**. El
número va separado de su letra por varios espacios (`V   12.345.678`), y en la
vista previa el hueco salía angosto. Se corrigió con `xml:space="preserve"` en
cada `<text>` (y recortando el espaciado de Jinja alrededor del contenido). Hay
una prueba que lo fija, porque es un fallo silencioso: no rompe nada, solo deja
de parecerse.

**Verificación.** Se recorrió el trámite, se capturó `/exito` en un navegador de
verdad y se comparó contra el PDF descargado en la misma corrida, rasterizado y
reescalado al mismo tamaño:

- Posición de cada elemento (número, oficina, apellidos, nombres, etiquetas,
  las cuatro casillas, nacionalidad, huella): coinciden dentro del **0,2 % – 0,9 %**
  del lado de la tarjeta.
- La huella: **1 píxel de diferencia sobre 1000** (previa x 18..196 y 438..658;
  PDF x 18..197 y 438..659).
- La imagen de diferencia solo muestra bordes, es decir, antialiasing del
  rasterizador; no hay ningún elemento desplazado.

**Pruebas** (suite de 42 → **49 casos**). `TestVistaPreviaEspejoDelPDF` fija la
correspondencia: un texto de la previa por cada campo del anverso, con la misma
posición y el mismo cuerpo; las cajas de firma/huella/foto iguales a las que
estampa el PDF; el reverso con sus textos y su QR; la separación del número; y
que se condense solo lo que no cabe. En `tests/test_routes.py`, que `/exito`
dibuje las dos caras, con la huella del dedo elegido y con `xml:space`.
