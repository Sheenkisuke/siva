import unittest
from unittest import mock

import numpy as np

from app.utils import photo_validator as pv
from app.utils.photo_validator import validar_foto


class TestValidator(unittest.TestCase):
    def test_dimension_validation(self):
        # Asegurarnos de que devuelva una estructura esperada
        resultado = validar_foto("ruta/inexistente.jpg")
        self.assertIsInstance(resultado, dict)
        self.assertIn("valida", resultado)
        self.assertIn("errores", resultado)
        self.assertFalse(resultado["valida"])


class TestUmbralFondoConfigurable(unittest.TestCase):
    """
    Verifica que el umbral de fondo claro (config.FONDO_THRESHOLD) sea configurable:
    una misma foto con 52.4% de fondo claro debe RECHAZARSE con umbral 70 y
    ACEPTARSE con umbral 40. Se simulan las etapas previas (rostro, gafas, etc.)
    para llegar de forma determinista a la comprobación del fondo.
    """

    def _validar_con(self, porcentaje_fondo, umbral):
        arr = np.zeros((448, 336, 3), dtype='uint8')
        with mock.patch.multiple(pv, CV2_DISPONIBLE=True, CASCADA_DISPONIBLE=True), \
             mock.patch.object(pv, 'cv2', create=True) as m_cv2, \
             mock.patch.object(pv, '_es_imagen_grafica_o_placeholder', return_value=False), \
             mock.patch.object(pv, '_verificar_dimensiones_cv2', return_value=(True, 'ok', arr)), \
             mock.patch.object(pv, '_detectar_rostro', return_value=[(10, 10, 100, 100)]), \
             mock.patch.object(pv, '_detectar_ojos', return_value=[(1, 1, 5, 5), (2, 2, 5, 5)]), \
             mock.patch.object(pv, '_detectar_gafas', return_value=False), \
             mock.patch.object(pv, '_detectar_gorra', return_value=False), \
             mock.patch.object(pv, '_verificar_fondo_blanco', return_value=porcentaje_fondo), \
             mock.patch('os.path.exists', return_value=True):
            m_cv2.imread.return_value = arr
            m_cv2.cvtColor.return_value = arr
            return validar_foto('foto.png', umbral_fondo=umbral)

    def test_fondo_bajo_rechazado_con_umbral_alto(self):
        self.assertFalse(self._validar_con(52.4, umbral=70.0)['valida'])

    def test_fondo_bajo_aceptado_con_umbral_bajo(self):
        self.assertTrue(self._validar_con(52.4, umbral=40.0)['valida'])


class TestConfigDesdeEntorno(unittest.TestCase):
    """
    Verifica que los umbrales se leen de variables de entorno. Se usa un
    subproceso porque config.py se evalúa al importarse (una sola vez). Al pasar
    la variable en el entorno, load_dotenv() no la sobrescribe con el .env.
    """

    def _leer_config(self, var, valor):
        import os
        import subprocess
        import sys
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        salida = subprocess.check_output(
            [sys.executable, '-c', f'from config import Config; print(Config.{var})'],
            env={**os.environ, var: valor}, cwd=raiz, text=True,
        )
        return float(salida.strip())

    def test_fondo_threshold_configurable(self):
        self.assertEqual(self._leer_config('FONDO_THRESHOLD', '33'), 33.0)

    def test_facial_threshold_configurable(self):
        self.assertEqual(self._leer_config('FACIAL_THRESHOLD', '0.5'), 0.5)

    def test_facial_tolerance_configurable(self):
        self.assertEqual(self._leer_config('FACIAL_TOLERANCE', '0.42'), 0.42)


if __name__ == '__main__':
    unittest.main()
