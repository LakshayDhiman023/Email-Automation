# Mailflow — one-command dev workflow.
#   make install   first-time setup (backend venv + frontend deps)
#   make migrate   apply pending DB migrations   ·  make seed  example templates
#   make backend   run the API                   ·  make frontend  run the dashboard
#   make test / lint / build                     ·  make check  everything CI runs

PY := backend/.venv/bin/python

.PHONY: install migrate seed backend frontend test lint build check

install:
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install -r backend/requirements-dev.txt
	cd frontend && npm install

migrate:
	cd backend && .venv/bin/python scripts/migrate.py

seed:
	cd backend && .venv/bin/python scripts/seed_templates.py

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/python -m pytest tests/ -q

lint:
	cd backend && .venv/bin/ruff check app/ scripts/ tests/
	cd frontend && npm run lint

build:
	cd frontend && npm run build

check: lint test build
