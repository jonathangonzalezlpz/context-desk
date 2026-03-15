.PHONY: setup dev lint test docker-up docker-down

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
