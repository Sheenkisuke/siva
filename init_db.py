import os
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from app import create_app, db
from app.models import Usuario

app = create_app()

# Dedos por ciudadano que puede consultar el selector de huellas de /renovacion.
TOTAL_DEDOS = 10

def generar_fotos(cedula, color_bg, iniciales):
    ruta_fotos = os.path.join('static', 'fotos')
    os.makedirs(ruta_fotos, exist_ok=True)
    ruta = os.path.join(ruta_fotos, f"{cedula}.png")
    
    img = Image.new('RGB', (336, 448), color='#E0E0E0')
    draw = ImageDraw.Draw(img)
    
    # Silueta simple
    draw.ellipse((118, 100, 218, 200), fill=color_bg)
    draw.polygon([(168, 200), (80, 448), (256, 448)], fill=color_bg)
    
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except IOError:
        font = ImageFont.load_default()
        
    draw.text((168, 300), iniciales, fill="white", font=font, anchor="mm")
    img.save(ruta)
    
def generar_firmas(cedula):
    ruta_firmas = os.path.join('static', 'firmas')
    os.makedirs(ruta_firmas, exist_ok=True)
    ruta = os.path.join(ruta_firmas, f"{cedula}.png")
    
    img = Image.new('RGB', (300, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Patrón tipo firma aleatorio
    points = [
        (10, 50),
        (50, random.randint(20, 80)),
        (100, random.randint(20, 80)),
        (150, random.randint(20, 80)),
        (200, random.randint(20, 80)),
        (250, 50)
    ]
    draw.line(points, fill="#00008B", width=3, joint="curve")
    img.save(ruta)

def _dibujar_huella(ruta, aleatorio):
    """
    Dibuja un patrón de huella (óvalos concéntricos) y lo guarda en `ruta`.

    Args:
        aleatorio: instancia de random.Random ya sembrada. Se recibe sembrada a
            propósito: las huellas se versionan en el repositorio, así que usar
            el `random` global generaría un archivo distinto en cada `make seed`
            y ensuciaría el historial con diferencias que no aportan nada.
    """
    img = Image.new('RGB', (200, 250), color='white')
    draw = ImageDraw.Draw(img)

    # Patrón de huella: óvalos concéntricos alrededor de un núcleo. Lo que varía
    # por dedo es el núcleo (desplazado), la excentricidad del óvalo, la
    # separación entre anillos y la inclinación final. Variar solo el número de
    # anillos NO basta: las diez huellas salen prácticamente idénticas y el
    # selector de dedos pierde sentido.
    nucleo_x = 100 + aleatorio.randint(-20, 20)
    nucleo_y = 125 + aleatorio.randint(-18, 18)
    radio_x = aleatorio.randint(22, 40)
    radio_y = aleatorio.randint(30, 54)
    separacion = aleatorio.randint(7, 11)
    anillos = aleatorio.randint(9, 13)

    for i in range(anillos):
        rx = radio_x + i * separacion
        ry = radio_y + i * separacion
        draw.ellipse((nucleo_x - rx, nucleo_y - ry, nucleo_x + rx, nucleo_y + ry),
                     outline="darkgray", width=2)

    # Inclinación: cada dedo apoya la yema con un ángulo distinto.
    img = img.rotate(aleatorio.randint(-28, 28), fillcolor='white')
    img.save(ruta)


def generar_huellas(cedula, ruta_base=None):
    """
    Genera las huellas del ciudadano:

    - `<cedula>.png`: la huella principal, que es la que estampa el PDF
      (`Usuario.huella_ruta`).
    - `<cedula>_1.png` … `<cedula>_10.png`: una huella por dedo, que es lo que
      muestra el selector de huellas de la vista de renovación. El número es
      solo el índice del archivo; el dedo al que corresponde lo define DEDOS en
      app/routes.py.

    Args:
        ruta_base: carpeta destino. Por defecto `static/huellas`.
    """
    ruta_huellas = ruta_base or os.path.join('static', 'huellas')
    os.makedirs(ruta_huellas, exist_ok=True)

    _dibujar_huella(os.path.join(ruta_huellas, f"{cedula}.png"), random.Random(cedula))
    for dedo in range(1, TOTAL_DEDOS + 1):
        _dibujar_huella(os.path.join(ruta_huellas, f"{cedula}_{dedo}.png"),
                        random.Random(f"{cedula}-{dedo}"))
    
def generar_bandera():
    ruta_img = os.path.join('static', 'img')
    os.makedirs(ruta_img, exist_ok=True)
    ruta = os.path.join(ruta_img, "bandera.png")
    
    img = Image.new('RGB', (120, 80), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 120, 26], fill="#FCD116") # Amarillo
    draw.rectangle([0, 27, 120, 53], fill="#003DA5") # Azul
    draw.rectangle([0, 54, 120, 80], fill="#CE1126") # Rojo
    
    img.save(ruta)

def init_db():
    """
    Inicializa la base de datos con los usuarios de prueba.
    """
    with app.app_context():
        # Crear base de datos y tablas
        db.drop_all()
        db.create_all()
        
        usuarios_data = [
            ("V-12345678", "Carlos Eduardo", "Rodríguez Pérez", "1990-03-15", "M", "Soltero", "carlos123"),
            ("V-23456789", "María Gabriela", "González López", "1985-07-22", "F", "Casada", "maria123"),
            ("V-34567890", "José Antonio", "Martínez Díaz", "1978-11-08", "M", "Casado", "jose123"),
            ("V-45678901", "Ana Carolina", "Hernández Silva", "1995-01-30", "F", "Soltera", "ana123"),
            ("V-56789012", "Luis Fernando", "Ramírez Torres", "1982-05-14", "M", "Divorciado", "luis123"),
            ("V-67890123", "Daniela Alejandra", "Morales Castro", "1970-09-03", "F", "Viuda", "daniela123"),
            ("V-78901234", "Pedro Miguel", "López Gutiérrez", "1988-12-25", "M", "Casado", "pedro123"),
            ("V-89012345", "Valentina Isabel", "Flores Rivas", "1999-04-17", "F", "Soltera", "valentina123"),
            ("V-90123456", "Andrés Felipe", "Vargas Mendoza", "1965-08-09", "M", "Viudo", "andres123"),
            ("V-10234567", "Sofía Alejandra", "Paredes Herrera", "1992-06-28", "F", "Divorciada", "sofia123")
        ]
        
        colores = ['#4A90E2', '#50E3C2', '#B8E986', '#F5A623', '#D0021B', '#9013FE', '#8B572A', '#417505', '#4A4A4A', '#F8E71C']
        
        for idx, (cedula, nombres, apellidos, fecha_nac, sexo, est_civil, pwd) in enumerate(usuarios_data):
            u = Usuario(
                cedula=cedula,
                nombres=nombres,
                apellidos=apellidos,
                fecha_nacimiento=datetime.strptime(fecha_nac, '%Y-%m-%d').date(),
                sexo=sexo,
                estado_civil=est_civil,
                foto_ruta=f"fotos/{cedula}.png",
                firma_ruta=f"firmas/{cedula}.png",
                huella_ruta=f"huellas/{cedula}.png"
            )
            u.establecer_contrasena(pwd)
            db.session.add(u)
            
            iniciales = f"{nombres[0]}{apellidos[0]}"
            generar_fotos(cedula, colores[idx % len(colores)], iniciales)
            generar_firmas(cedula)
            generar_huellas(cedula)
            
        generar_bandera()
        db.session.commit()
        print("Base de datos inicializada correctamente con usuarios de prueba y archivos generados.")

if __name__ == "__main__":
    init_db()
