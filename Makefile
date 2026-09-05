PYTHON ?= .venv/bin/python

.PHONY: setup verify phase1-validate smoke kaggle-bundle kaggle-bundle-validate test lint typecheck check code-map

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

kaggle-bundle:
	$(PYTHON) scripts/prepare_kaggle_phase1.py --owner huylmhuhu --dataset-version 5

kaggle-bundle-validate:
	$(PYTHON) scripts/validate_kaggle_bundle.py

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy src scripts

check: verify phase1-validate lint typecheck test

code-map:
	$(PYTHON) scripts/generate_code_map.py
