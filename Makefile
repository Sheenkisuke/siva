# Makefile del Proyecto SIVA
# Automatiza los comandos descritos en el README (ver sección "Instalación y Ejecución").
#
# Uso rápido:
#   make install   -> crea el entorno virtual e instala dependencias
#   make seed      -> inicializa y siembra la base de datos
#   make run       -> arranca el servidor en http://127.0.0.1:5000
#
# El intérprete por defecto es python3.12 (versión con wheels compatibles para
# pillow/opencv). Para usar otro: make install PYTHON=python3.13

PYTHON ?= python3.12
VENV   := venv
BIN    := $(VENV)/bin
STAMP  := $(VENV)/.installed

.DEFAULT_GOAL := help
.PHONY: help venv install biometria seed run test clean clean-uploads

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

venv: $(BIN)/activate ## Crea el entorno virtual (venv)

$(BIN)/activate:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip

install: $(STAMP) ## Crea el venv e instala las dependencias (requirements.txt)

$(STAMP): requirements.txt | $(BIN)/activate
	$(BIN)/pip install -r requirements.txt
	@touch $(STAMP)

biometria: install ## (Opcional) Activa el reconocimiento facial real (face_recognition + dlib)
	$(BIN)/pip install --no-deps -r requirements-biometria.txt

seed: install ## Inicializa y siembra la base de datos (init_db.py)
	$(BIN)/python init_db.py

run: install ## Arranca el servidor de desarrollo (run.py)
	$(BIN)/python run.py

test: install ## Ejecuta las pruebas unitarias
	$(BIN)/python -m unittest discover -s tests -v

clean-uploads: ## Borra las fotos y PDFs subidos/generados en static/uploads
	rm -rf static/uploads/*

clean: ## Elimina venv, base de datos y cachés de Python
	rm -rf $(VENV)
	rm -rf data
	rm -rf .pytest_cache
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
