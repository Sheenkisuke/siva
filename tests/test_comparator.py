import unittest
from app.utils.face_comparator import comparar_rostros

class TestComparator(unittest.TestCase):
    def test_comparador_estructura(self):
        resultado = comparar_rostros("foto1.jpg", "foto2.jpg")
        self.assertIsInstance(resultado, dict)
        self.assertIn("porcentaje_similitud", resultado)
        self.assertIn("coincide", resultado)
        self.assertIn("mensaje", resultado)
