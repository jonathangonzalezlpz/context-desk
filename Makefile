.PHONY: setup dev lint test docker-up docker-down ingest-catalog ingest-knowledge run down

COMPOSE_FILE = docker/files/docker-compose.yml

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
	docker-compose -f $(COMPOSE_FILE) up -d

docker-down:
	docker-compose -f $(COMPOSE_FILE) down

# Unified Actions
run:
	bash docker/actions/run.sh $(ARGS)

down:
	bash docker/actions/down.sh

ingest-catalog:
	docker-compose -f $(COMPOSE_FILE) exec -T api python knowledge/processed/farmacia_demo/scripts/ingest_catalog.py

ingest-knowledge:
	docker-compose -f $(COMPOSE_FILE) exec -T api python knowledge/processed/farmacia_demo/scripts/ingest_knowledge.py
