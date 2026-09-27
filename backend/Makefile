PY ?= python3.12
VENV := .venv
BIN := $(VENV)/bin
COMPOSE := docker compose -f ../infra/docker-compose.yml

.PHONY: install lock db-up db-down migrate migration seed seed-full run lint format typecheck test check openapi help

install:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -c requirements.lock -e ".[dev]"

# Пересобрать lock-файл в том же образе, что и Dockerfile: версии под Linux, а не под эту машину.
lock:
	docker run --rm -v "$(CURDIR)":/src:ro python:3.12-slim sh -c \
		'cp -r /src /tmp/b && cd /tmp/b && rm -rf .venv && pip install -q --root-user-action=ignore . \
		&& pip freeze --exclude radar-vuzov-backend' | grep '==' > requirements.lock.new
	{ head -2 requirements.lock; cat requirements.lock.new; } > requirements.lock.tmp
	mv requirements.lock.tmp requirements.lock && rm requirements.lock.new

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

migrations-check:
	$(BIN)/alembic upgrade head
	$(BIN)/alembic check

check: lint typecheck migrations-check test

openapi:
	$(BIN)/python -m scripts.export_openapi

help:
	$(BIN)/python -m scripts.export_help

docs-pdf:
	$(BIN)/python -m scripts.export_docs_pdf
