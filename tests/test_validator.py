import unittest
from app.utils.photo_validator import validar_foto

class TestValidator(unittest.TestCase):
    def test_dimension_validation(self):
        # Asegurarnos de que devuelva una estructura esperada
        resultado = validar_foto("ruta/inexistente.jpg")
        self.assertIsInstance(resultado, dict)
        self.assertIn("valida", resultado)
        self.assertIn("errores", resultado)
        self.assertFalse(resultado["valida"])
