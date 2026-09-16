PY ?= python3.12
VENV := .venv
BIN := $(VENV)/bin
COMPOSE := docker compose -f ../infra/docker-compose.yml

.PHONY: install db-up db-down migrate migration seed seed-full run lint format typecheck test check openapi

install:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

db-up:
	$(COMPOSE) up -d postgres redis

db-down:
	$(COMPOSE) down

migrate:
	$(BIN)/alembic upgrade head

migration:
	$(BIN)/alembic revision --autogenerate -m "$(name)"

seed:
	$(BIN)/python -m scripts.seed

seed-full:
	$(BIN)/python -m scripts.seed --full

run:
	$(BIN)/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

lint:
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

format:
	$(BIN)/ruff check --fix .
	$(BIN)/ruff format .

typecheck:
	$(BIN)/mypy app scripts

test:
	$(BIN)/pytest

check: lint typecheck test

openapi:
	$(BIN)/python -m scripts.export_openapi
