PYTHON ?= .venv/bin/python

.PHONY: setup verify phase1-validate smoke test lint typecheck check code-map

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements-dev.txt

verify:
	$(PYTHON) scripts/verify_setup.py

phase1-validate:
	$(PYTHON) scripts/build_smoke_environment.py
	$(PYTHON) scripts/validate_smoke_data.py
	$(PYTHON) scripts/verify_phase1.py

smoke: phase1-validate
	$(PYTHON) scripts/run_smoke.py --backend replay

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy src scripts

check: verify phase1-validate lint typecheck test

code-map:
	$(PYTHON) scripts/generate_code_map.py
