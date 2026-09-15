# Архитектура «Радар вузов»

Версия 0 от 15.09.2026 — **черновик на согласование** бэкендом и фронтендом. После согласования меняется только PR с одобрением обоих людей; каждое изменение архитектуры — запись в разделе «Решения».

CRM для сотрудников ИТ Школы Ростелекома (кейс №6 ЛЦТ 2026). Ведёт каждое взаимодействие с вузом по настраиваемому workflow из 14 этапов, сама находит, где процесс застрял (радар), и показывает, какие программы востребованы (рейтинг).

## 1. Решения

| ID | Решение | Почему |
|---|---|---|
| ADR-001 | Центральная запись — **взаимодействие = вуз × ИТ-программа × ИТ-продукт**. Вуз — контейнер; договор может покрывать несколько взаимодействий | Совпадает со строкой отчёта из ТЗ; статус передачи и обучение идут по каждому продукту отдельно |
| ADR-002 | Бэкенд: Python 3.12, FastAPI, SQLAlchemy 2 (async, asyncpg), Alembic, PostgreSQL 16+, Redis 7, воркер arq | Разрешено ТЗ; бэкендер уверенно читает Python |
| ADR-003 | Фронтенд: React 19, Vite, TypeScript, Tailwind 4, shadcn/ui на Radix, TanStack Query | Фактический стек первого дня |
| ADR-004 | Контракт `contracts/openapi.yaml` генерируется из FastAPI командой `make openapi`; CI сверяет его со схемой приложения; изменения одобряют оба | Один источник правды без ручной синхронизации |
| ADR-005 | История переходов `transition` только дописывается (триггер БД); этап на любую дату вычисляется из истории | Отчёты за прошлые периоды показывают статусы того времени |
| ADR-006 | Радар и рейтинг детерминированные и объяснимые, без внешних LLM | 152-ФЗ, надёжность демо, проверяемость экспертами |
| ADR-007 | Ошибки — `application/problem+json` с полем `code` из каталога (раздел 5). Запись вне области видимости — `404 NOT_FOUND` | Коды ошибок из ТЗ; не раскрываем существование чужих данных |
| ADR-008 | Пагинация — конверт `{items, total, page, page_size}` | Проще для сгенерированного клиента, чем заголовок `X-Total-Count` |
| ADR-009 | Защита от параллельных изменений — поле `expected_version` в теле перехода; при расхождении `409 INTERACTION_VERSION_CONFLICT` | Два пользователя не перезапишут этап друг друга |
| ADR-010 | Поток событий SSE с заголовком `Authorization` (клиент на fetch), без токена в URL | Токены не попадают в журналы прокси |
| ADR-011 | Локальная разработка без Keycloak: `AUTH_MODE=dev` и заголовок `X-Dev-User`; режим запрещён при `APP_ENV=production` | Фронтенд и тесты работают без поднятого Keycloak |

## 2. Компоненты

| Сервис | Технология | Назначение |
|---|---|---|
| `web` | nginx | Отдаёт SPA, проксирует `/api` и `/auth`, TLS на стенде |
| `api` | FastAPI + uvicorn | REST `/api/v1`, SSE `/api/v1/events`, Swagger UI `/api/docs` |
| `worker` | arq | Отчёты, импорт, синхронизация LMS и сайта, пересчёт радара и рейтинга, подсказки норм |
| `postgres` | PostgreSQL 16+ | Доменные данные, история, витрины |
| `redis` | Redis 7 | Очередь, кэш справочников и рейтинга, pub/sub событий |
| `keycloak` | Keycloak 26+ | Вход OIDC, роли, политики паролей и сессий |
| `mock-lms`, `mock-site` | FastAPI | Данные LMS и заявки сайта по контракту, пока нет доступа заказчика |

Вложения хранятся через слой `Storage`: локальный том на стенде, S3-совместимое хранилище в продакшене.

### Структура бэкенда

```text
backend/
├── app/
│   ├── main.py            # сборка приложения, роутеры, обработчики ошибок
│   ├── core/              # config, db, errors, security, pagination
│   └── modules/
│       ├── catalogs/      # вузы, направления, программы, продукты, пользователи
│       ├── workflow/      # шаблоны, версии, этапы, правила, нормы
│       ├── interactions/  # взаимодействия, договоры, переходы, заметки, вложения
│       └── radar/         # сигналы
├── migrations/            # Alembic
├── scripts/               # экспорт OpenAPI, демо-данные
└── tests/
```

Слои модуля: `router.py` (HTTP) → `service.py` (правила и область видимости) → `repository.py` (запросы) → `models.py` / `schemas.py`. Роутеры не обращаются к БД напрямую.

### Ключевые потоки

1. **Смена этапа (p95 ≤ 1 с).** SPA сразу показывает новый этап → `POST /api/v1/interactions/{id}/transitions` с `expected_version` → сервис проверяет область видимости и правило перехода → одна транзакция: запись в `transition` и обновление `interaction` → пересчёт сигналов этого взаимодействия → событие в Redis → SSE владельцу и руководителю.
2. **Отчёт.** `POST /api/v1/reports` → `202` и id задания → воркер строит xlsx (openpyxl), xls (xlwt), json или pdf (HTML-шаблон и headless Chromium; графики ECharts по тем же настройкам, что в интерфейсе) → прогресс по SSE → скачивание.
3. **Импорт xls/xlsx.** Загрузка → маппинг колонок → предпросмотр → применение: каталоги, договоры и взаимодействия; даты подписания и срока лицензии пишутся в историю → пересчёт радара.
4. **Интеграции.** Воркер по расписанию получает JSON из LMS (Moodle Web Services, СЭО 3KL) и сайта → месячные метрики → заявка сопоставляется с взаимодействием по (вуз, программа, продукт) или создаёт новое на первом этапе.

## 3. Модель данных (PostgreSQL)

Конвенции: PK `id uuid`; `created_at`, `updated_at` — `timestamptz` в UTC; у каталогов мягкое удаление `archived_at`; перечисления — `text` + `CHECK`; внешние ключи `ON DELETE RESTRICT`. База создаётся с локалью UTF-8 — в локали `C` поиск без учёта регистра не работает для кириллицы. Нотация: `поле → таблица` — внешний ключ.

### Каталоги

```text
university        id, name UNIQUE, short_name, region, city, is_priority2030, archived_at
direction         id, code UNIQUE, name
program           id, direction_id → direction, name, lms_course_ref
vendor            id, name UNIQUE
product           id, vendor_id → vendor, name
product_direction PK(product_id, direction_id)
program_product   PK(program_id, product_id), is_default        -- программа по продукту при импорте
contact_person    id, university_id → university, full_name, position, email_enc, phone_enc   -- ПДн
team              id, name, manager_user_id → app_user
app_user          id, keycloak_sub UNIQUE, email UNIQUE, full_name, role (kam|manager|admin), team_id → team, is_active
```

### Workflow

```text
workflow_template     id, name, is_default, archived_at
workflow_version      id, template_id → workflow_template, version_no, status (draft|published|retired), published_at
stage                 id, version_id → workflow_version, code, name, position, kind (start|normal|final),
                      bulk_allowed, required_document_types text[]
stage_transition_rule id, version_id, from_stage_id → stage, to_stage_id → stage, requires_comment, requires_attachment
stage_norm            id, template_id, stage_code, norm_days, source (manual|suggested),
                      suggested_median_days, sample_size
```

Базовый шаблон, 14 этапов:

| № | Код | Название |
|---|---|---|
| 1 | `contact_search` | Поиск контактов |
| 2 | `communication` | Коммуникация |
| 3 | `meeting` | Встреча |
| 4 | `documents_exchange` | Обмен документами |
| 5 | `documents_revision` | Доработка документов (необязательный) |
| 6 | `signing` | Подписание |
| 7 | `materials_transfer` | Передача материалов |
| 8 | `implementation_support` | Поддержка внедрения |
| 9 | `teacher_training` | Обучение преподавателей |
| 10 | `curriculum_update` | Обновление программы |
| 11 | `classes` | Ведение занятий |
| 12 | `docs_update` | Обновление документации |
| 13 | `teacher_upskilling` | Повышение квалификации |
| 14 | `stage_control` | Контроль этапов (финальный) |

- Переход по умолчанию — на следующий этап; с «Обмена документами» можно сразу на «Подписание», минуя доработку. Комментарий обязателен для каждого перехода.
- Обязательные документы: «Подписание» — подписанный договор, «Передача материалов» — акт передачи, «Обучение преподавателей» — подтверждение обучения.
- Переименование этапа допустимо в опубликованной версии. Добавление, удаление и перестановка создают новую версию; открытые взаимодействия переносятся по карте «старый код → новый этап».

### Взаимодействия

```text
contract           id, university_id → university, number, signed_at, license_signed_at, license_valid_until,
                   license_term_years, transfer_status, UNIQUE(university_id, number)
interaction        id, university_id, program_id, product_id, contract_id → contract, workflow_version_id,
                   current_stage_id → stage, stage_entered_at, owner_user_id → app_user,
                   status (active|paused|completed|cancelled), source (manual|import|site|lms|demo),
                   version, last_activity_at, UNIQUE(university_id, program_id, product_id) WHERE status <> 'cancelled'
interaction_contact PK(interaction_id, contact_person_id), role
transition         id, interaction_id, from_stage_id, to_stage_id, occurred_at, actor_user_id, comment,
                   source (manual|bulk|import|integration|migration)        -- только INSERT
interaction_note   id, interaction_id, author_user_id, text
attachment         id, interaction_id, transition_id, stage_id, document_type, file_name, mime_type,
                   size_bytes, sha256, storage_key, uploaded_by
assignment_change  id, interaction_id, from_user_id, to_user_id, changed_by, changed_at, reason
```

### Импорт, интеграции, аналитика, аудит

```text
import_profile     id, name, file_kind (xls|xlsx), column_map jsonb
import_batch       id, profile_id, file_name, status (uploaded|previewed|applied|failed), stats jsonb
import_row         id, batch_id, row_no, raw jsonb, resolution (new|update|conflict|skip|needs_program)
integration_source id, kind (lms|site), base_url, secret_ref, is_mock, schedule_cron, last_sync_at
sync_run           id, source_id, started_at, finished_at, status, stats jsonb, error_code
site_application   id, external_id UNIQUE, university_id, program_id, received_at, match_status, interaction_id
program_metric     id, university_id, program_id, period_month, metric (applications|students|streams), value, source
radar_signal       id, interaction_id, kind, severity (low|medium|high), detected_at, resolved_at, evidence jsonb,
                   UNIQUE(interaction_id, kind) WHERE resolved_at IS NULL
rating_weight_set  id, name, w_applications, w_students, w_streams, is_default   -- сумма весов 100
report_job         id, requested_by, params jsonb, status, progress, file_key, error_code
saved_view         id, user_id, page, name, filters jsonb, columns jsonb
data_access_rule   id, subject_user_id | subject_role, effect (allow|deny), scope_kind, scope_id
audit_log          id bigserial, occurred_at, actor_user_id, action, entity_kind, entity_id, before, after, trace_id  -- только INSERT
app_setting        key, value jsonb                    -- пороги радара, веса по умолчанию
```

Поля xlsx заказчика → модель: «Название ВУЗа» → `university`; «Вендор», «ПО» → `vendor`, `product`; «Номер договора», «Подписание лицензии», «Срок действия лицензии» → `contract`; «Статус по передаче» → `contract.transfer_status` и этап по карте значений; «ФИО Менеджера» → `interaction.owner_user_id`; «Ответственные от ВУЗа» → `contact_person`; «Комментарий» → `interaction_note`.

## 4. Доступ и роли

| Роль | Видит взаимодействия | Может сверх просмотра |
|---|---|---|
| `kam` — КАМ | свои (`owner_user_id` = пользователь) | переходы, комментарии, файлы в своих взаимодействиях |
| `manager` — руководитель | своей команды и свои | назначать и снимать ответственных, веса рейтинга, импорт, workflow |
| `admin` — администратор | все | пользователи, правила доступа к данным, интеграции, настройки, аудит |

- Keycloak: realm `radar-vuzov`, публичный клиент `radar-web` (Authorization Code + PKCE), аудитория API `radar-api`, роли в claim `realm_access.roles`.
- При первом входе пользователь создаётся в `app_user` по `sub` и email из токена; роль берётся из токена, команда — из БД.
- Область видимости применяет сервисный слой ко всем запросам; запись вне области — `404 NOT_FOUND`.
- Страницы и доступ к разделам по ролям — [`docs/FRONTEND_PAGES.md`](docs/FRONTEND_PAGES.md).

## 5. API

- Префикс `/api/v1`, JSON, даты ISO 8601 в UTC. Swagger UI — `/api/docs`, схема — `/api/openapi.json`, копия — `contracts/openapi.yaml`.
- Списки: `?page=1&page_size=50` (максимум 200) → `{items, total, page, page_size}`. Одинаковые фильтры у списков, отчётов и JSON-выгрузки: `period_from`, `period_to`, `university_id`, `direction_id`, `program_id`, `product_id`, `owner_id`, `stage_code`, `search` (повторяемые параметры для множественного выбора).
- Авторизация: `Authorization: Bearer <access_token>`.

### Методы v0

| Метод | Назначение |
|---|---|
| `GET /api/health` | Состояние сервиса и БД |
| `GET /api/v1/me` | Профиль: id, ФИО, роль, команда, область видимости |
| `GET /api/v1/universities`, `/{id}` | Вузы со счётчиками взаимодействий и открытых сигналов |
| `GET /api/v1/directions`, `/programs`, `/products`, `/users` | Справочники |
| `GET /api/v1/workflows/default` | Опубликованная версия базового workflow с этапами и правилами |
| `GET /api/v1/interactions` | Взаимодействия с фильтрами: вуз, программа, продукт, КАМ, этап, дни на этапе, версия, открытые сигналы |
| `GET /api/v1/interactions/{id}` | Карточка: договор, история, допустимые переходы с требованиями, сигналы |
| `POST /api/v1/interactions/{id}/transitions` | Переход: `to_stage_id`, `comment`, `expected_version`, `attachment_ids` |
| `GET /api/v1/signals` | Открытые сигналы радара с доказательствами |

Следующие версии контракта: вложения и импорт (v1, 19.09), SSE и отчёты (22.09), рейтинг, статистика и администрирование (24.09).

### Формат ошибки

```json
{
  "type": "about:blank",
  "title": "Нужен комментарий",
  "status": 422,
  "code": "WF_COMMENT_REQUIRED",
  "detail": "Добавьте комментарий: без него переход на этап «Подписание» недоступен.",
  "trace_id": "8f2c1b4e9a0d4c7e",
  "errors": [{ "field": "comment", "message": "Обязательное поле" }]
}
```

### Каталог кодов ошибок

| Код | HTTP | Когда |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Неверные параметры запроса; подробности в `errors` |
| `AUTH_REQUIRED` | 401 | Нет токена или он просрочен |
| `AUTH_FORBIDDEN` | 403 | Роль не позволяет действие |
| `NOT_FOUND` | 404 | Записи нет или она вне области видимости |
| `INTERACTION_VERSION_CONFLICT` | 409 | Запись уже изменил другой пользователь |
| `WF_TRANSITION_NOT_ALLOWED` | 409 | Переход в выбранный этап не разрешён правилами |
| `WF_COMMENT_REQUIRED` | 422 | Для перехода нужен комментарий |
| `WF_ATTACHMENT_REQUIRED` | 422 | Для перехода нужен документ |
| `FILE_TYPE_NOT_ALLOWED` | 415 | Тип файла вне белого списка ТЗ |
| `FILE_TOO_LARGE` | 413 | Файл больше лимита |
| `IMPORT_MAPPING_INVALID` | 422 | Маппинг колонок не покрывает обязательные поля |
| `REPORT_TOO_LARGE` | 422 | Отчёт превышает лимит строк |
| `INTEGRATION_UNAVAILABLE` | 502 | LMS или сайт не ответили |
| `INTERNAL_ERROR` | 500 | Непредвиденная ошибка; `trace_id` для поиска в журнале |

## 6. Радар и рейтинг

### Сигналы

| Вид | Условие | Серьёзность |
|---|---|---|
| `stage_overdue` | дней на этапе больше нормы | medium — больше нормы, high — больше двух норм |
| `license_expiring` | до `license_valid_until` 60 дней или меньше | medium — до 60, high — до 30 или истекла |
| `missing_document` | этап требует документ, файла нужного типа нет | medium |
| `inactivity` | нет переходов, заметок и файлов | low — от 21 дня, medium — от 42 |

- У сигнала есть `evidence`: этап, дни, норма и её источник, дата лицензии или последнего действия — всё, чтобы эксперт пересчитал вручную.
- Пересчёт — сразу по событию (переход, файл, договор, импорт) и раз в сутки для всех. Исправленное условие закрывает сигнал (`resolved_at`).
- Нормы задаёт руководитель; когда накопится не меньше 5 завершённых этапов, система предлагает медиану.

### Рейтинг востребованности

```text
n_m   = 100 × value_m / max(value_m внутри направления)
score = Σ(w_m × n_m) / Σ(w_m)      веса по умолчанию: заявки 40, обучающиеся 40, потоки 20
contrib_m = w_m × n_m / Σ(w_m)     сумма вкладов равна баллу
```

Нет метрики за период — она исключается, веса перераспределяются, позиция помечается «неполные данные».

## 7. Безопасность (152-ФЗ, приказ ФСТЭК №117)

- **Вход:** Keycloak, пароль от 12 символов, блокировка после 5 неудачных попыток, простой сессии 30 минут; SPA — Authorization Code + PKCE.
- **Доступ:** роль + область видимости + правила администратора; тест «чужая запись недоступна» на каждый эндпоинт.
- **Журнал:** `audit_log` хранит изменения и просмотр персональных данных, значения до и после.
- **Данные:** TLS; email и телефон контактов шифруются в приложении; белый список типов файлов; секреты только в окружении; персональные данные не пишутся в логи.
- **Целостность:** история и аудит только дописываются; ежедневный `pg_dump` с проверкой восстановления.
- **Уязвимости:** `pip-audit`, `npm audit`, `gitleaks` в CI.
- Данные хранятся на серверах в РФ; на демо-стенде только синтетические данные.

## 8. Нефункциональные требования и проверка

| Требование | Как проверяем |
|---|---|
| Отклик ≤ 1 с | k6: p95 < 1000 мс при 50 виртуальных пользователях |
| 10 параллельных отчётов | k6 запускает 10 заданий, p95 API остаётся < 1 с |
| Без перезагрузки | e2e: переход и событие SSE без навигации |
| Коды ошибок | Тесты на каждый код каталога |
| Swagger и перечень библиотек | `/api/docs`; перечень генерирует CI |
| Docker и Linux | `docker compose up` в CI на Ubuntu |

## 9. Открытые вопросы

- Подтвердить фронтенду: realm, client ID, redirect URI `http://127.0.0.1:5173/*` и claim ролей.
- Получить у организаторов пример xls/xlsx и контракты API LMS и сайта.
- Решение по гранту облака для стенда — до 25.09.
