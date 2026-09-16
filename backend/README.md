# Бэкенд «Радар вузов»

API на FastAPI. Архитектура — [`ARCHITECTURE.md`](../ARCHITECTURE.md), правила потока — [`AGENTS.md`](AGENTS.md), план — [`docs/PLAN.md`](../docs/PLAN.md).

## Запуск

Нужны Python 3.12 и PostgreSQL 16 с локалью UTF-8 — проще всего через Docker.

```bash
cp .env.example .env
make install
make db-up      # PostgreSQL на порту 55432 и Redis в Docker
make migrate
make seed       # базовый workflow и 6 демо-связок из фронтенд-фикстур
make run        # Swagger UI: http://127.0.0.1:8000/api/docs
```

PostgreSQL публикуется на 55432, потому что 5432 на машине разработчика обычно занят локальным сервером. Адреса с этим портом уже прописаны в `.env.example`; внутри compose адрес остаётся `postgres:5432`.

Ночные задачи — полный пересчёт радара и подсказки норм — выполняет воркер arq: `arq app.worker.WorkerSettings` или сервис `worker` в `infra/docker-compose.yml`. Без Redis API работает: события тогда живут в памяти процесса.

Для демонстрации и нагрузочных проверок есть полный стенд: `make seed-full` — 96 вузов, около 350 взаимодействий, год истории переходов и месячные показатели программ. Стенд детерминирован (`random.Random(2026)`), шесть связок из `make seed` сохраняются, повторный запуск ничего не дублирует.

Без Keycloak при `AUTH_MODE=dev` пользователь передаётся заголовком `X-Dev-User`:

| Email | Роль |
|---|---|
| `anna.smirnova@example.com` | КАМ |
| `mikhail.volkov@example.com` | КАМ |
| `roman.kovalev@example.com` | руководитель |
| `alina.denisova@example.com` | администратор |

```bash
curl -H "X-Dev-User: anna.smirnova@example.com" http://127.0.0.1:8000/api/v1/signals
```

Полное окружение с Keycloak: `docker compose -f ../infra/docker-compose.yml up`. Демо-входы: `kam.demo`, `manager.demo`, `admin.demo`. Пароли в `infra/keycloak/realm-radar-vuzov.json` — только для локальной разработки.

## Для фронтенда

- API: `http://127.0.0.1:8000`; CORS разрешён для `http://127.0.0.1:5173` и `http://localhost:5173`.
- Keycloak: `http://127.0.0.1:8080`, realm `radar-vuzov`, клиент `radar-web` (публичный, PKCE S256), redirect `http://127.0.0.1:5173/*`, роли в claim `realm_access.roles`.
- Вложения: `multipart/form-data` с полями `file` и `document_type`; допустимы png, jpg, jpeg, pdf, zip, gz, rar, doc, docx, xls, xlsx в пределах `MAX_UPLOAD_MB` (25 МБ). Файл скачивается по `GET /api/v1/attachments/{id}/file`.
- Контракт: [`contracts/openapi.yaml`](../contracts/openapi.yaml).

## Проверки

`make check` — ruff, mypy и pytest. Для тестов нужен PostgreSQL из `make db-up` или адрес в `TEST_DATABASE_URL`. После изменения API — `make openapi` и коммит обновлённого контракта.
