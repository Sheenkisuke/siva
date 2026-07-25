"""
Pruebas de generación de PDF y del arreglo #3 (fecha de vencimiento en años bisiestos).
"""
import io
import os
import tempfile
import unittest
from datetime import date

from PIL import Image

from app import create_app
from app.models import Usuario
from app.utils.pdf_generator import generar_cedula_pdf
from app.utils.qr_generator import sumar_anios
from config import Config


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True


def _imagen_temporal():
    ruta = os.path.join(tempfile.mkdtemp(), 'foto.png')
    Image.new('RGB', (336, 448), color='#8899AA').save(ruta)
    return ruta


class TestSumarAnios(unittest.TestCase):
    def test_anio_normal(self):
        self.assertEqual(sumar_anios(date(2020, 1, 15), 10), date(2030, 1, 15))

    def test_29_de_febrero_no_crashea(self):
        """#3: 29-feb + 10 años (año destino no bisiesto) antes lanzaba ValueError."""
        self.assertEqual(sumar_anios(date(2024, 2, 29), 10), date(2034, 2, 28))


class TestGenerarPDF(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_genera_pdf_valido(self):
        u = Usuario(
            cedula='V-99999999', nombres='Test', apellidos='User',
            fecha_nacimiento=date(1990, 1, 1), sexo='M', estado_civil='Soltero',
        )
        salida = os.path.join(tempfile.mkdtemp(), 'cedula.pdf')
        ruta = generar_cedula_pdf(u, _imagen_temporal(), salida)
        self.assertIsNotNone(ruta)
        self.assertTrue(os.path.exists(ruta))
        self.assertGreater(os.path.getsize(ruta), 1000)
        with open(ruta, 'rb') as f:
            self.assertTrue(f.read(4) == b'%PDF')  # cabecera de PDF válida


if __name__ == '__main__':
    unittest.main()
