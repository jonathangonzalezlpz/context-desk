.PHONY: setup dev lint test docker-up docker-down ingest-catalog ingest-knowledge

setup:
	uv pip install -e ".[dev]"
	pre-commit install

dev:
	uvicorn backend.src.app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check .
	ruff format --check .
	mypy backend/src/app

test:
	pytest backend/tests -v

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

ingest-catalog:
	python knowledge/processed/farmacia_demo/scripts/ingest_catalog.py

ingest-knowledge:
	python knowledge/processed/farmacia_demo/scripts/ingest_knowledge.py
