.PHONY: up test lint format typecheck model

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
