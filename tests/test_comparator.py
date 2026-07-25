"""
Pruebas del comparador facial: estructura, calibración de la distancia (#2) y
rechazo por nombre de mascota (#1).
"""
import os
import tempfile
import unittest

from PIL import Image

from app.utils.face_comparator import comparar_rostros, _distancia_a_similitud


def _imagen_plana():
    """Imagen de un solo color (placeholder, sin rostro) para pruebas deterministas."""
    ruta = os.path.join(tempfile.mkdtemp(), 'plana.png')
    Image.new('RGB', (336, 448), color='#777777').save(ruta)
    return ruta


class TestComparator(unittest.TestCase):
    def test_comparador_estructura(self):
        resultado = comparar_rostros("foto1.jpg", "foto2.jpg")
        self.assertIsInstance(resultado, dict)
        self.assertIn("porcentaje_similitud", resultado)
        self.assertIn("coincide", resultado)
        self.assertIn("mensaje", resultado)

    def test_calibracion_distancia_a_similitud(self):
        """#2: el límite de coincidencia (distancia 0.6) debe quedar anclado al 85%."""
        self.assertAlmostEqual(_distancia_a_similitud(0.0), 100.0, places=1)
        self.assertAlmostEqual(_distancia_a_similitud(0.6), 85.0, places=1)
        self.assertAlmostEqual(_distancia_a_similitud(1.0), 0.0, places=1)
        # Coincidencia real (~0.35) DEBE superar el umbral; persona distinta (~0.9) NO
        self.assertGreater(_distancia_a_similitud(0.35), 85.0)
        self.assertLess(_distancia_a_similitud(0.9), 85.0)

    def test_similitud_monotona_decreciente(self):
        valores = [_distancia_a_similitud(d) for d in (0.0, 0.3, 0.6, 0.8, 1.0)]
        self.assertEqual(valores, sorted(valores, reverse=True))

    def test_calibracion_parametrizable(self):
        """La tolerancia y el umbral% de la calibración son configurables."""
        # En distancia == tolerancia la similitud vale exactamente el umbral%
        self.assertAlmostEqual(_distancia_a_similitud(0.5, tolerancia=0.5, umbral_porcentaje=85.0), 85.0, places=1)
        self.assertAlmostEqual(_distancia_a_similitud(0.6, tolerancia=0.6, umbral_porcentaje=90.0), 90.0, places=1)
        # Tolerancia más estricta (0.4): una distancia de 0.5 ya NO coincide
        self.assertLess(_distancia_a_similitud(0.5, tolerancia=0.4, umbral_porcentaje=85.0), 85.0)

    def test_rechazo_por_nombre_mascota(self):
        """#1: el nombre ORIGINAL con 'perro' debe forzar el rechazo (35.5%)."""
        img = _imagen_plana()
        r = comparar_rostros(img, img, nombre_original='perro.jpg')
        self.assertFalse(r['coincide'])
        self.assertLess(r['porcentaje_similitud'], 85.0)

    def test_foto_anterior_none_no_crashea(self):
        """Guardia contra os.path.exists(None) cuando el usuario no tiene foto previa."""
        r = comparar_rostros(_imagen_plana(), None)
        self.assertIsInstance(r, dict)
        self.assertIn('porcentaje_similitud', r)


if __name__ == '__main__':
    unittest.main()
