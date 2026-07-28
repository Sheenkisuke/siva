"""
Pruebas de generación de PDF y del arreglo #3 (fecha de vencimiento en años bisiestos).
"""
import io
import os
import tempfile
import unittest
from datetime import date

import numpy as np
from PIL import Image

from app import create_app
from app.models import Usuario
from app.utils.pdf_generator import (
    generar_cedula_pdf, _partes_cedula, _serial_oficina, _nacionalidad,
    datos_anverso, _especificacion_anverso, vista_previa,
    VB_ANCHO, VB_ALTO, FIRMA_CAJA, HUELLA_CAJA, FOTO_CAJA, TEXTOS_REVERSO,
)
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


class TestFormatoDeDatosDelCarnet(unittest.TestCase):
    """Cómo se imprimen los datos en el anverso."""

    def test_cedula_se_agrupa_en_miles(self):
        self.assertEqual(_partes_cedula('V-12345678'), ('V', '12.345.678'))
        self.assertEqual(_partes_cedula('E-1234567'), ('E', '1.234.567'))
        self.assertEqual(_partes_cedula('V-123'), ('V', '123'))

    def test_cedula_sin_prefijo_asume_venezolano(self):
        self.assertEqual(_partes_cedula('12345678'), ('V', '12.345.678'))

    def test_nacionalidad_segun_prefijo(self):
        self.assertEqual(_nacionalidad('V-12345678'), 'VENEZOLANO')
        self.assertEqual(_nacionalidad('E-12345678'), 'EXTRANJERO')

    def test_serial_de_oficina_estable_y_de_tres_digitos(self):
        self.assertEqual(_serial_oficina('V-12345678'), _serial_oficina('V-12345678'))
        self.assertEqual(len(_serial_oficina('V-12345678')), 3)
        self.assertEqual(len(_serial_oficina('')), 3)


def _huella_plana():
    """Huella de prueba de un color plano: comprime a muy pocos bytes."""
    ruta = os.path.join(tempfile.mkdtemp(), 'huella_plana.png')
    Image.new('RGB', (200, 250), color='white').save(ruta)
    return ruta


def _huella_ruidosa():
    """Huella de prueba con ruido aleatorio: comprime muchísimo peor que la plana."""
    ruta = os.path.join(tempfile.mkdtemp(), 'huella_ruido.png')
    Image.fromarray((np.random.rand(250, 200, 3) * 255).astype('uint8')).save(ruta)
    return ruta


class TestHuellaEstampadaEnElPDF(unittest.TestCase):
    """
    La huella del PDF debe ser la del dedo elegido en el selector de /renovacion.
    """

    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.foto = _imagen_temporal()

    def tearDown(self):
        self.ctx.pop()

    def _usuario(self, huella_ruta=None):
        return Usuario(
            cedula='V-99999999', nombres='Test', apellidos='User',
            fecha_nacimiento=date(1990, 1, 1), sexo='M', estado_civil='Soltero',
            huella_ruta=huella_ruta,
        )

    def _generar(self, ruta_huella, huella_ruta=None):
        salida = os.path.join(tempfile.mkdtemp(), 'cedula.pdf')
        return generar_cedula_pdf(self._usuario(huella_ruta), self.foto, salida,
                                  ruta_huella=ruta_huella)

    def test_la_huella_elegida_se_incrusta_de_verdad(self):
        """
        Una huella plana y una ruidosa pesan muy distinto al comprimirse. Si el
        PDF de la ruidosa es mucho más grande, la imagen elegida se está
        incrustando de verdad. Comparar los bytes enteros no serviría: ReportLab
        nombra los XObject con un hash de la ruta, así que dos archivos distintos
        darían PDFs distintos aunque no se dibujara ninguno de los dos.
        """
        plano = os.path.getsize(self._generar(_huella_plana()))
        ruidoso = os.path.getsize(self._generar(_huella_ruidosa()))
        self.assertGreater(ruidoso - plano, 20000,
                           f"plano={plano} ruidoso={ruidoso}: la huella no se incrusta")

    def test_si_la_huella_elegida_no_existe_cae_en_la_principal(self):
        """Una ruta inexistente no debe romper el PDF ni dejarlo sin huella."""
        inexistente = os.path.join(tempfile.mkdtemp(), 'no_esta.png')
        ruta = self._generar(inexistente)
        self.assertIsNotNone(ruta)
        self.assertTrue(os.path.exists(ruta))
        with open(ruta, 'rb') as f:
            self.assertEqual(f.read(4), b'%PDF')

    def test_sin_huella_indicada_sigue_generando(self):
        ruta = self._generar(None)
        self.assertIsNotNone(ruta)
        self.assertGreater(os.path.getsize(ruta), 1000)


class TestVistaPreviaEspejoDelPDF(unittest.TestCase):
    """
    La vista previa de /exito se dibuja con la misma maquetación que el PDF.
    Estas pruebas fijan esa correspondencia: si alguien mueve un campo del PDF y
    la vista previa no lo acompaña (o al revés), aquí se rompe.
    """

    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.usuario = Usuario(
            cedula='V-12345678', nombres='Carlos Eduardo', apellidos='Rodríguez Pérez',
            fecha_nacimiento=date(1990, 3, 15), sexo='M', estado_civil='Soltero',
        )

    def tearDown(self):
        self.ctx.pop()

    def test_un_texto_de_la_previa_por_cada_campo_del_anverso(self):
        esperados = [t for t in _especificacion_anverso(datos_anverso(self.usuario)) if t.texto]
        obtenidos = vista_previa(self.usuario)['anverso']['textos']
        self.assertEqual(len(obtenidos), len(esperados))
        for esperado, obtenido in zip(esperados, obtenidos):
            self.assertEqual(obtenido['texto'], esperado.texto)
            self.assertAlmostEqual(obtenido['x'], round(esperado.x * VB_ANCHO, 2), places=2)
            self.assertAlmostEqual(obtenido['y'], round(esperado.y * VB_ALTO, 2), places=2)
            self.assertAlmostEqual(obtenido['cuerpo'], round(esperado.cuerpo * VB_ALTO, 2),
                                   places=2)

    def test_las_cajas_de_imagen_son_las_mismas_que_estampa_el_pdf(self):
        imagenes = vista_previa(self.usuario)['anverso']['imagenes']
        for clave, caja in (('firma', FIRMA_CAJA), ('huella', HUELLA_CAJA),
                            ('foto', FOTO_CAJA)):
            x, y_sup, ancho, alto = caja
            self.assertAlmostEqual(imagenes[clave]['x'], round(x * VB_ANCHO, 2), places=2)
            self.assertAlmostEqual(imagenes[clave]['y'], round(y_sup * VB_ALTO, 2), places=2)
            self.assertAlmostEqual(imagenes[clave]['ancho'], round(ancho * VB_ANCHO, 2),
                                   places=2)
            self.assertAlmostEqual(imagenes[clave]['alto'], round(alto * VB_ALTO, 2), places=2)

    def test_el_reverso_lleva_sus_textos_y_el_qr(self):
        reverso = vista_previa(self.usuario)['reverso']
        self.assertEqual(len(reverso['textos']), len(TEXTOS_REVERSO))
        self.assertTrue(reverso['qr']['src'].startswith('data:image/png;base64,'))

    def test_el_numero_de_cedula_conserva_la_separacion(self):
        """
        El hueco entre la letra y el número son varios espacios. SVG los colapsa
        salvo con xml:space="preserve", así que el dato debe llegar con ellos
        para que la plantilla los pueda preservar.
        """
        cedula = next(t for t in vista_previa(self.usuario)['anverso']['textos']
                      if t['texto'].lstrip().startswith('V '))
        self.assertIn('   ', cedula['texto'])

    def test_condensa_solo_lo_que_no_cabe(self):
        """
        El ajuste horizontal replica el del PDF: 'spacingAndGlyphs' equivale a la
        escala horizontal (Tz) y 'spacing' al charSpace (Tc) del encabezado.
        """
        textos = {t['texto']: t for t in vista_previa(self.usuario)['anverso']['textos']}
        titulo = textos['REPUBLICA BOLIVARIANA DE VENEZUELA']
        self.assertEqual(titulo['ajuste'], 'spacing')
        self.assertIsNotNone(titulo['largo'])
        # 'Director' entra de sobra en su hueco: no debe tocarse
        self.assertIsNone(textos['Director']['largo'])
        self.assertIsNone(textos['Director']['ajuste'])

    def test_el_viewbox_conserva_la_proporcion_de_la_tarjeta(self):
        previa = vista_previa(self.usuario)
        from app.utils.pdf_generator import PROPORCION_TARJETA
        self.assertAlmostEqual(previa['ancho'] / previa['alto'], PROPORCION_TARJETA, places=3)


if __name__ == '__main__':
    unittest.main()
