.PHONY: setup dev seed demo-cache demo test e2e eval lint docker-up clean

VENV ?= .venv
PYTHON ?= $(VENV)/bin/python3
PIP ?= $(VENV)/bin/pip
PYTEST ?= $(VENV)/bin/pytest
UVICORN ?= $(VENV)/bin/uvicorn

setup:
	test -d $(VENV) || python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Setup complete. Virtual environment ready in $(VENV)."

dev:
	@echo "Starting MedGuard API..."
	$(UVICORN) backend.app.main:app --reload --port 8000 &
	cd frontend && npm run dev

seed:
	$(PYTHON) scripts/import_lexicon.py
	$(PYTHON) scripts/seed_all.py

demo-cache:
	$(PYTHON) scripts/prewarm_cache.py

demo: seed demo-cache
	@echo "Starting MedGuard in offline DEMO mode on http://localhost:8000 ..."
	$(UVICORN) backend.app.main:app --port 8000

test:
	$(PYTEST) -v backend/tests

eval:
	$(PYTHON) eval/run_eval.py

lint:
	@echo "Checking syntax and types..."
	$(PYTHON) -m py_compile backend/app/main.py

docker-up:
	docker compose up --build

clean:
	rm -rf __pycache__ .pytest_cache backend/**/__pycache__

