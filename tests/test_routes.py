"""
Pruebas de integración del flujo de renovación usando el cliente de pruebas de Flask.

Estas pruebas ejercitan las RUTAS reales (login, subida de foto, éxito, PDF) y
verifican DECISIONES de aceptación/rechazo, no solo la estructura de la respuesta.
Cubren especialmente el arreglo #1 (rechazo por nombre de mascota) que antes no
funcionaba porque el archivo se renombraba antes de la comparación.
"""
import io
import os
import shutil
import tempfile
import unittest
from datetime import date

import numpy as np
from PIL import Image, ImageDraw

import init_db
from app import create_app, db
from app.models import Usuario
from app.routes import DEDOS
from config import Config


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'clave-de-pruebas'


def _ruido_png():
    """Imagen 336x448 de ruido aleatorio: muchos colores (NO placeholder), sin rostro."""
    arr = (np.random.rand(448, 336, 3) * 255).astype('uint8')
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, 'PNG')
    return buf.getvalue()


def _placeholder_png():
    """Avatar de silueta con pocos colores (<400): activa el bypass de validación,
    igual que los avatares que genera init_db.py. Es determinista y no depende de
    archivos del repositorio (que el usuario puede haber reemplazado)."""
    img = Image.new('RGB', (336, 448), color='#E0E0E0')
    d = ImageDraw.Draw(img)
    d.ellipse((118, 100, 218, 200), fill='#4A90E2')
    d.polygon([(168, 200), (80, 448), (256, 448)], fill='#4A90E2')
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    return buf.getvalue()


class TestFlujoRenovacion(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        # Guardar subidas y PDFs en un directorio temporal para no ensuciar el repo
        self.tmp_uploads = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.tmp_uploads
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Referencia (foto "anterior") auto-generada bajo static/uploads para no
        # depender de static/fotos/*.png (que el usuario puede haber reemplazado).
        self.ref_rel = 'uploads/_test_ref_V12345678.png'
        self.ref_path = os.path.join(self.app.static_folder, self.ref_rel)
        os.makedirs(os.path.dirname(self.ref_path), exist_ok=True)
        with open(self.ref_path, 'wb') as f:
            f.write(_placeholder_png())

        u = Usuario(
            cedula='V-12345678', nombres='Carlos', apellidos='Rodríguez',
            fecha_nacimiento=date(1990, 3, 15), sexo='M', estado_civil='Soltero',
            foto_ruta=self.ref_rel, firma_ruta='firmas/V-12345678.png',
            huella_ruta='huellas/V-12345678.png',
        )
        u.establecer_contrasena('carlos123')
        db.session.add(u)
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        shutil.rmtree(self.tmp_uploads, ignore_errors=True)
        if os.path.exists(self.ref_path):
            os.remove(self.ref_path)

    # -- helpers ----------------------------------------------------------
    def _login(self, password='carlos123'):
        return self.client.post('/login', data={'cedula': 'V-12345678', 'password': password})

    def _subir(self, filename, content=None):
        if content is None:
            content = _placeholder_png()
        return self.client.post(
            '/verificar-foto',
            data={'foto': (io.BytesIO(content), filename)},
            content_type='multipart/form-data',
        )

    # -- pruebas ----------------------------------------------------------
    def test_login_correcto_redirige_a_dashboard(self):
        r = self._login()
        self.assertEqual(r.status_code, 302)
        self.assertIn('/dashboard', r.headers['Location'])

    def test_login_incorrecto_muestra_error(self):
        r = self._login('clave-erronea')
        self.assertEqual(r.status_code, 200)  # re-renderiza el login
        self.assertIn('incorrecta', r.get_data(as_text=True).lower())

    def test_flujo_exitoso_genera_pdf_descargable(self):
        self._login()
        r = self._subir('mi_foto.png')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/exito', r.headers['Location'])

        pdf = self.client.get('/descargar-pdf')
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.headers['Content-Type'], 'application/pdf')
        self.assertGreater(len(pdf.get_data()), 1000)

    def test_rechazo_por_nombre_de_mascota(self):
        """#1: un archivo llamado 'perro.png' debe RECHAZARSE aunque se renombre al guardarlo."""
        self._login()
        r = self._subir('perro.png')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/subir-foto', r.headers['Location'])  # rechazado, NO llega a /exito

    def test_rechazo_foto_sin_rostro(self):
        self._login()
        r = self._subir('foto.png', content=_ruido_png())
        self.assertIn('/subir-foto', r.headers['Location'])

    def test_bloqueo_tras_tres_intentos_fallidos(self):
        self._login()
        destinos = [self._subir('x.png', content=_ruido_png()).headers['Location'] for _ in range(3)]
        self.assertIn('/subir-foto', destinos[0])
        self.assertIn('/subir-foto', destinos[1])
        self.assertIn('/dashboard', destinos[2])  # bloqueado al 3er intento


class TestSelectorHuellas(unittest.TestCase):
    """
    Selector de huellas de /renovacion: las dos manos con los 10 dedos
    seleccionables, cada uno apuntando a la huella de ese dedo.
    """

    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        u = Usuario(
            cedula='V-12345678', nombres='Carlos', apellidos='Rodríguez',
            fecha_nacimiento=date(1990, 3, 15), sexo='M', estado_civil='Soltero',
            foto_ruta='fotos/V-12345678.png', firma_ruta='firmas/V-12345678.png',
            huella_ruta='huellas/V-12345678.png',
        )
        u.establecer_contrasena('carlos123')
        db.session.add(u)
        db.session.commit()

        self.client = self.app.test_client()
        self.client.post('/login', data={'cedula': 'V-12345678', 'password': 'carlos123'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _html(self):
        respuesta = self.client.get('/renovacion')
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.get_data(as_text=True)

    def test_se_dibujan_los_diez_puntos(self):
        self.assertEqual(self._html().count('class="huella-punto"'), 10)

    def test_cada_punto_apunta_a_la_huella_de_su_dedo(self):
        html = self._html()
        for dedo in DEDOS:
            self.assertIn(f'huellas/V-12345678_{dedo["numero"]}.png', html)
            self.assertIn(f'data-nombre="{dedo["nombre"]}"', html)

    def test_los_puntos_se_ubican_en_porcentaje(self):
        """
        Las coordenadas van en % (no en px) para que el centro del punto siga
        cayendo sobre la yema cuando el panel se redimensiona.
        """
        html = self._html()
        for dedo in DEDOS:
            self.assertIn(f'left: {dedo["x"]}%; top: {dedo["y"]}%;', html)

    def test_dedos_declarados_sin_huecos_ni_repetidos(self):
        self.assertEqual([d['numero'] for d in DEDOS], list(range(1, 11)))
        self.assertEqual(len({d['nombre'] for d in DEDOS}), 10)

    def test_requiere_sesion(self):
        """
        /renovacion no es pública. Se levanta una app aparte a propósito:
        Flask-Login cachea el usuario en `g`, que vive en el CONTEXTO DE
        APLICACIÓN que setUp mantiene abierto, así que reutilizar esa app haría
        pasar por autenticado a un cliente sin sesión (y la prueba mentiría).
        """
        otra = create_app(TestConfig)
        with otra.app_context():
            respuesta = otra.test_client().get('/renovacion')
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/login', respuesta.headers['Location'])


class TestGeneracionDeHuellas(unittest.TestCase):
    """init_db genera la huella principal (la que estampa el PDF) y una por dedo."""

    def test_genera_la_principal_mas_una_por_dedo(self):
        with tempfile.TemporaryDirectory() as destino:
            init_db.generar_huellas('V-99999999', ruta_base=destino)
            archivos = os.listdir(destino)
            self.assertEqual(len(archivos), init_db.TOTAL_DEDOS + 1)
            self.assertIn('V-99999999.png', archivos)
            for n in range(1, init_db.TOTAL_DEDOS + 1):
                self.assertIn(f'V-99999999_{n}.png', archivos)

    def test_cada_dedo_tiene_un_patron_distinto(self):
        with tempfile.TemporaryDirectory() as destino:
            init_db.generar_huellas('V-99999999', ruta_base=destino)
            patrones = set()
            for n in range(1, init_db.TOTAL_DEDOS + 1):
                with open(os.path.join(destino, f'V-99999999_{n}.png'), 'rb') as f:
                    patrones.add(f.read())
            self.assertEqual(len(patrones), init_db.TOTAL_DEDOS)

    def test_regenerar_produce_archivos_identicos(self):
        """
        Las huellas se versionan en el repositorio: la semilla debe ser estable
        para que un `make seed` no genere diferencias en cada corrida.
        """
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            init_db.generar_huellas('V-99999999', ruta_base=a)
            init_db.generar_huellas('V-99999999', ruta_base=b)
            for nombre in os.listdir(a):
                with open(os.path.join(a, nombre), 'rb') as fa, \
                     open(os.path.join(b, nombre), 'rb') as fb:
                    self.assertEqual(fa.read(), fb.read(), nombre)


if __name__ == '__main__':
    unittest.main()
