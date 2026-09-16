# Бэкенд — правила потока

Дополняет корневой [`AGENTS.md`](../AGENTS.md). Архитектура и модель данных — [`ARCHITECTURE.md`](../ARCHITECTURE.md), порядок задач — [`docs/PLAN.md`](../docs/PLAN.md), раздел «Бэкенд», содержание каждой задачи — [`docs/BACKEND_PLAN.md`](../docs/BACKEND_PLAN.md).

## Стек

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 (async, asyncpg) · Alembic · PostgreSQL 16+ · Redis 7 · arq · pytest · ruff · mypy.

## Команды

Все команды выполняются из папки `backend/`.

| Команда | Что делает |
|---|---|
| `make install` | Создаёт `.venv` и ставит зависимости с dev-инструментами |
| `make db-up` | Поднимает PostgreSQL и Redis через `infra/docker-compose.yml` |
| `make migrate` | Применяет миграции (`alembic upgrade head`) |
| `make seed` | Загружает базовый workflow и демо-данные v0 |
| `make run` | Запускает API с автоперезагрузкой на http://127.0.0.1:8000 |
| `make lint` | `ruff check` и `ruff format --check` |
| `make typecheck` | `mypy app` |
| `make test` | `pytest` (нужен PostgreSQL из `make db-up` или `TEST_DATABASE_URL`) |
| `make check` | lint, typecheck и test — обязательно перед PR |
| `make openapi` | Экспортирует схему в `../contracts/openapi.yaml` |
| `make migration name=...` | Новая миграция Alembic |

## Структура модуля

```text
app/modules/<модуль>/
├── models.py      # таблицы SQLAlchemy
├── schemas.py     # модели запросов и ответов Pydantic
├── repository.py  # запросы к БД, без бизнес-правил
├── service.py     # правила, область видимости, транзакции
└── router.py      # HTTP: только разбор запроса и вызов сервиса
```

## Правила

- **Область видимости.** Любой запрос к взаимодействиям и связанным данным идёт через `app/core/scope.py`. Запись вне области — `NOT_FOUND`, а не `AUTH_FORBIDDEN`.
- **Ошибки.** Только через `AppError` с кодом из каталога в `ARCHITECTURE.md`. Непредвиденное исключение превращается в `INTERNAL_ERROR` с `trace_id`; стек — только в журнал.
- **Транзакции.** Одна бизнес-операция — одна транзакция в сервисе. Переход пишет `transition` и обновляет `interaction` вместе.
- **История.** `transition` и `audit_log` только дописываются. Не писать UPDATE и DELETE для них даже в тестах.
- **Миграции.** Только добавляются; у каждой есть `downgrade`. Применённую миграцию не редактировать. Изменение модели — миграция в том же PR.
- **Время.** Только `datetime` с часовым поясом в UTC. Даты договоров и лицензий — `date`.
- **Запросы.** Без N+1: связи загружать через `selectinload` или `joinedload`. Поля фильтров — с индексами.
- **Контракт.** После изменения API выполнить `make openapi` и закоммитить `contracts/openapi.yaml`; такой PR одобряют оба человека.
- **Тесты.** На каждый эндпоинт: успешный сценарий, чужая запись недоступна, коды ошибок. Данные — только синтетические, из фабрик в `tests/`. Без `sleep` и без сети.
- **Логи.** Без персональных данных и токенов. Идентификатор запроса — `trace_id`.
- **Локаль БД.** PostgreSQL создаётся с локалью UTF-8: в локали `C` поиск `ILIKE` не учитывает регистр кириллицы, и фильтры перестают находить «ИТМО» по запросу «итмо».

## Режим разработки

При `APP_ENV=local` и `AUTH_MODE=dev` API принимает заголовок `X-Dev-User: <email>` вместо токена Keycloak — только для локальной работы и тестов. При `APP_ENV=production` этот режим не запускается.
