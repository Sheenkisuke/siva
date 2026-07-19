# Guía de Modificación Visual del PDF (Anverso Izquierdo)

Esta guía explica detalladamente cómo está estructurado el posicionamiento de elementos en la parte izquierda del anverso de la cédula en PDF y cómo puedes modificar la posición de la foto del usuario (moverla a la derecha, centrarla, cambiar el tamaño, etc.) dentro del archivo [pdf_generator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/pdf_generator.py).

---

## 📐 Estructura del Anverso en ReportLab

La cédula se dibuja como un rectángulo físico de **8.9 cm x 5.4 cm**. Todo se posiciona utilizando coordenadas X e Y en puntos (donde `cm` es la unidad de centímetros importada de `reportlab.lib.units`).

En [pdf_generator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/pdf_generator.py), el anverso izquierdo inicia en:
*   `x_anverso = 2 * cm` (Margen izquierdo de la página)
*   `y_tarjeta = 20 * cm` (Margen inferior de la página)
*   `ancho_tarjeta = 8.9 * cm`
*   `alto_tarjeta = 5.4 * cm`

Cualquier posición de elemento se calcula **relativa** a estas variables.

---

## 📸 Modificación de la Foto de Perfil del Ciudadano

El código que dibuja la foto del usuario en el anverso izquierdo se encuentra en las líneas 59-64 de [pdf_generator.py](file:///C:/Users/User1/.gemini/antigravity/scratch/SIVA/app/utils/pdf_generator.py):

```python
# Foto del usuario
try:
    c.drawImage(ruta_foto_nueva, x_anverso + 0.2 * cm, y_tarjeta + 1.2 * cm, width=2.5*cm, height=3*cm)
except Exception as e:
    logger.warning(f"No se pudo cargar la foto: {e}")
    c.rect(x_anverso + 0.2 * cm, y_tarjeta + 1.2 * cm, 2.5*cm, 3*cm)
```

La función `c.drawImage` toma los siguientes argumentos en orden:
`c.drawImage(ruta_imagen, x, y, width, height)`

*   `x`: Posición horizontal inicial.
*   `y`: Posición vertical inicial.
*   `width`: Ancho de la imagen (2.5 cm por defecto).
*   `height`: Alto de la imagen (3.0 cm por defecto).

---

## 🔄 Opciones de Alineación y Posicionamiento de la Foto

Si deseas modificar la posición de la foto para centrarla, moverla a la derecha, o cambiar su tamaño en el anverso, debes alterar el parámetro `x` e `y` en la llamada a `c.drawImage` (y su respectivo bloque `except` que dibuja el rectángulo de fallback).

A continuación se muestran los tres ejemplos prácticos con las fórmulas de coordenadas correctas:

### Opción 1: Alinear la foto a la DERECHA del anverso izquierdo
Para mover la foto al extremo derecho del anverso izquierdo (cerca del borde del doblez), calculamos la posición restando el ancho de la foto y un pequeño margen del ancho total de la tarjeta (`ancho_tarjeta`):

```python
# Calcular la X en el extremo derecho:
# x_anverso (borde izquierdo) + ancho_tarjeta (borde derecho) - ancho_foto (2.5 cm) - margen (0.2 cm)
x_foto = x_anverso + ancho_tarjeta - 2.5 * cm - 0.2 * cm
y_foto = y_tarjeta + 1.2 * cm  # Mantiene la altura vertical

try:
    c.drawImage(ruta_foto_nueva, x_foto, y_foto, width=2.5*cm, height=3*cm)
except Exception as e:
    c.rect(x_foto, y_foto, 2.5*cm, 3*cm)
```
> [!NOTE]  
> Si mueves la foto a la derecha, tendrás que mover los textos de nombres, apellidos y cédula hacia la izquierda (ej. cambiando `x_anverso + 3 * cm` a `x_anverso + 0.2 * cm`) en el código de abajo para que no se superpongan.

---

### Opción 2: CENTRAR la foto horizontalmente en el anverso izquierdo
Si deseas un diseño de credencial vertical donde la foto esté exactamente en el centro del anverso izquierdo:

```python
# Fórmula de centrado:
# x_anverso + (ancho_tarjeta / 2) - (ancho_foto / 2)
x_foto = x_anverso + (ancho_tarjeta / 2) - (2.5 * cm / 2)
# Puedes ajustar la Y a tu gusto (por ejemplo, subirla un poco más en la tarjeta)
y_foto = y_tarjeta + 1.5 * cm 

try:
    c.drawImage(ruta_foto_nueva, x_foto, y_foto, width=2.5*cm, height=3*cm)
except Exception as e:
    c.rect(x_foto, y_foto, 2.5*cm, 3*cm)
```

---

### Opción 3: Alinear la foto a la IZQUIERDA (Diseño original por defecto)
Esta es la alineación original. Ubica la foto en el extremo izquierdo dejando la parte derecha libre para los datos del ciudadano:

```python
x_foto = x_anverso + 0.2 * cm
y_foto = y_tarjeta + 1.2 * cm

try:
    c.drawImage(ruta_foto_nueva, x_foto, y_foto, width=2.5*cm, height=3*cm)
except Exception as e:
    c.rect(x_foto, y_foto, 2.5*cm, 3*cm)
```

---

## 🎨 Agregar y centrar una Imagen de Fondo en el Anverso Izquierdo

Si deseas añadir una imagen de fondo o marca de agua (por ejemplo, un escudo nacional semitransparente o un mapa de Venezuela) en el anverso izquierdo de la tarjeta, debes hacerlo **antes** de escribir el texto y dibujar la foto de perfil para que los elementos principales queden encima.

### Ejemplo de código para añadir un fondo centrado con transparencia:

Añade este fragmento justo debajo del fondo del anverso (después de la línea 42):

```python
# --- IMAGEN DE FONDO EN ANVERSO ---
ruta_fondo = os.path.join(current_app.static_folder, "img", "bandera.png") # o "escudo.png"
if os.path.exists(ruta_fondo):
    c.saveState()
    # Definir transparencia de la marca de agua (0.15 = 15% opacidad)
    c.setFillAlpha(0.15)
    c.setStrokeAlpha(0.15)
    
    # Tamaño del fondo a dibujar
    ancho_fondo = 5 * cm
    alto_fondo = 3.5 * cm
    
    # Calcular coordenadas para centrar el fondo en la tarjeta
    x_fondo = x_anverso + (ancho_tarjeta / 2) - (ancho_fondo / 2)
    y_fondo = y_tarjeta + (alto_tarjeta / 2) - (alto_fondo / 2)
    
    # Dibujar fondo
    c.drawImage(ruta_fondo, x_fondo, y_fondo, width=ancho_fondo, height=alto_fondo, mask='auto')
    c.restoreState()
```

> [!TIP]  
> Utilizar `c.saveState()` y `c.restoreState()` es indispensable para asegurar que la opacidad (`setFillAlpha`) solo afecte a la imagen de fondo y no deje semitransparente el resto del texto o la foto del usuario.
