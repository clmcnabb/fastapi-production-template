.PHONY: up test lint format typecheck model db-init reset-db

up:
	docker compose up --build

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy app tests

model:
	uv run python scripts/create_dummy_model.py

db-init:
	docker compose up -d db
	docker compose run --rm api alembic upgrade head

reset-db:
	docker compose down -v
	find alembic/versions -maxdepth 1 -type f -name "*.py" -delete
	docker compose up -d db
	docker compose run --rm api alembic revision --autogenerate -m "initial schema"
	docker compose run --rm api alembic upgrade head
