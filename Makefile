PYTHON ?= .venv/bin/python

.PHONY: setup verify test lint typecheck check code-map

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements-dev.txt

verify:
	$(PYTHON) scripts/verify_setup.py

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy src scripts

check: verify lint typecheck test

code-map:
	$(PYTHON) scripts/generate_code_map.py
