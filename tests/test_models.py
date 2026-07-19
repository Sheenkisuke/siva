import unittest
from datetime import date
from app import create_app, db
from app.models import Usuario
from config import Config

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True

class TestModels(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self):
        u = Usuario(cedula="V-12345678", nombres="Juan", apellidos="Perez", 
                    fecha_nacimiento=date(1990, 1, 1), sexo="M", estado_civil="Soltero")
        u.establecer_contrasena("password123")
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.id is not None)

    def test_password_hashing(self):
        u = Usuario(cedula="V-12345678", nombres="Juan", apellidos="Perez", 
                    fecha_nacimiento=date(1990, 1, 1), sexo="M", estado_civil="Soltero")
        u.establecer_contrasena("secreto")
        self.assertFalse(u.verificar_contrasena("clave_erronea"))
        self.assertTrue(u.verificar_contrasena("secreto"))
