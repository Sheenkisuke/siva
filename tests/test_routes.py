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

from app import create_app, db
from app.models import Usuario
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


if __name__ == '__main__':
    unittest.main()
