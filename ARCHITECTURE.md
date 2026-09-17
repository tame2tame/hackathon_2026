# Архитектура «Радар вузов»

Версия 0 от 15.09.2026 — **черновик на согласование** бэкендом и фронтендом. После согласования меняется только PR с одобрением обоих людей; каждое изменение архитектуры — запись в разделе «Решения».

CRM для сотрудников ИТ Школы Ростелекома (кейс №6 ЛЦТ 2026). Ведёт взаимодействия с вузами (B2B, настраиваемый workflow из 14 этапов) и с частными лицами (B2C, свой процесс), сама находит, где процесс застрял (радар), и показывает, какие программы востребованы (рейтинг).

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
| ADR-012 | Фронтенд использует keycloak-js, openapi-typescript (типы из контракта), MSW (моки по тому же контракту) и Prettier для генерируемых файлов | Предложение фронтенда от 16.09; свои реализации этих задач дороже и хуже. Ждёт подтверждения в общем PR |
| ADR-013 | PDF отчёта строит `fpdf2` напрямую, без headless-браузера. Шрифт с кириллицей берётся из системы (`fonts-dejavu-core` в образе) | Chromium с Playwright добавляет около 400 МБ к образу и секунды на старт ради табличного файла. Цена вопроса — графики ECharts в PDF: их пока нет, в интерфейсе и JSON они остаются |
| ADR-014 | Процесс один на всех: изменения готовятся черновиком и при публикации применяются ко всем открытым записям. Записи с удалённого этапа сами переходят на ближайший предыдущий этап, а если его нет — на следующий; предпросмотр публикации показывает это до подтверждения. Переименование этапа — только администратор. У каждого перехода вперёд есть возврат на шаг назад с комментарием | Уточнения жюри 17.09 ([`docs/JURY_QA.md`](docs/JURY_QA.md)): версии не должны путать подразделения, изменение процесса не должно останавливать работу, переименование статусов чувствительно, а бюрократический процесс требует возвратов |
| ADR-015 | Взаимодействия делятся на **группы контрагентов** со своим процессом: «Вузы (B2B)» по базовому пути из ТЗ и «Частные лица (B2C)» по своему; администратор добавляет новые группы. Контрагент записи — ровно один: вуз или клиент (`client` — физическое или юридическое лицо). Продукт необязателен: программы бывают продуктозависимыми и продуктонезависимыми. Расширяет ADR-001 | Уточнения жюри 17.09: B2C «прямо в цель» — обучение частных и юридических лиц идёт по своему workflow; процесс меняется для группы целиком; программа управления проектами идёт с «Ягой», а часть программ — без продукта |
| ADR-016 | Уведомления: лента в интерфейсе и доставка в Telegram, Max и почту (SMTP) за общим интерфейсом отправителя. Доставка асинхронная через очередь `notification_delivery` с повторами (1, 5, 15, 60 минут, до пяти попыток); секрет канала — только имя переменной `NOTIFY_*`. Эскалация зависших записей идёт роли (руководитель команды КАМа или администраторы), а не человеку; срок — настройка `stalled_escalation` | Уточнения жюри 17.09: уведомления о смене этапов в Telegram, Max и подключаемую почту «хотя бы на заглушках»; зависшая заявка — уведомление вышестоящей роли через настраиваемый срок. Очередь не даёт медленному мессенджеру задерживать переход, а префикс переменных не позволяет через настройку канала вывести наружу чужой секрет |
| ADR-017 | Файлы вложений и отчётов лежат в S3-совместимом хранилище: MinIO на стенде и в локальном compose, в облаке — любое S3. Код работает через интерфейс `Storage`; `STORAGE_BACKEND=local` оставляет каталог на диске для разработки без контейнеров. Бакет создаётся при первом обращении, состояние хранилища входит в `/api/health` | Жюри назвало S3-хранилище (например MinIO) частью минимальной архитектуры и раздельное хранение файлов и реляционных данных — правильным подходом. Клиент `minio` работает с любым S3-совместимым сервисом и типизирован; образ MinIO с осени 2025 берётся с quay.io |
| ADR-018 | Обмен с LMS и CMS сайта двусторонний. Входящий — как раньше, по расписанию. Исходящий — transactional outbox: изменение записи в той же транзакции ставит отметку для каждого получателя, воркер раз в минуту строит документы `radar-vuzov/interaction@1` по последнему состоянию и отправляет пакетом JSON с повторами; тот же документ отдаёт API выгрузки (`updated_since` — забирать изменения по расписанию) | Жюри: CRM — ядро процесса с двусторонней интеграцией, обмен JSON по API синхронно или по расписанию, онлайн не нужен; в выгрузке статус, ответственный, вуз, программа, продукт и ключи связей с файлами в S3 и записями БД. Outbox не теряет изменения при отказе получателя и не шлёт ничего по откатившейся транзакции; контракт приёма — наш, пока заказчик не дал свой, и меняется только адаптер |
| ADR-019 | Импорт принимает CSV наравне с xls и xlsx: кодировка определяется по BOM, строгому UTF-8, иначе выбирается из cp1251, KOI8-R и cp866 по доле строчной кириллицы; разделитель — по образцу строк и подсказке Excel `sep=`; кодировку можно указать вручную. Отчёты выгружаются и в CSV — UTF-8 с BOM или cp1251. В табличных выгрузках значения, начинающиеся с `=`, `+`, `-`, `@`, экранируются апострофом | Жюри назвало кодировки «мелочью, на которой сыпятся»: файл должен загружаться и выгружаться без слетевшего формата. Своё определение из двух десятков строк проще и предсказуемее общей библиотеки для узкой задачи «русский текст в одной из четырёх кодировок»; апостроф закрывает CSV-инъекцию, когда выгрузку открывают в Excel |
| ADR-020 | Состояние записи (`active`, `paused`, `completed`, `cancelled`) отделено от этапа процесса и меняется методом `PUT /interactions/{id}/status` с причиной для паузы и отмены. Приостановленная запись не копит сигналы простоя и не участвует в переходах; отменённая уходит из рабочих списков, но остаётся в карточке, истории и отчёте с фильтром по состоянию; завершённую и отменённую можно вернуть в работу, если связка «вуз — программа — продукт» ещё свободна | Пауза и отмена — обычная жизнь сделки: вуз взял паузу до бюджета, заявка оказалась ошибочной. Без отдельного состояния такие записи либо висят просроченными в радаре, либо удаляются вместе с историей, а история по ТЗ только дописывается |
| ADR-021 | Порядок продвижения курсов задаётся вручную: `program.priority` от 0 до 100, справочник и рейтинг (`order=priority`) показывают отмеченные курсы первыми. Место и балл рейтинга при этом считаются только по данным и не меняются; приоритет правят руководитель и администратор, изменение пишется в аудит | Уточнение жюри 17.09: «приоритеты курсов можно и вручную». Данных LMS и сайта не хватает на решения вроде «в этом году продвигаем ИИ», но подменять ими расчётный рейтинг нельзя — иначе рейтинг перестаёт быть объяснимым (ADR-006) |
| ADR-022 | Кэш двухуровневый. На сервере в Redis лежат готовые ответы справочников и рейтинга: ключ содержит номер поколения, изменение справочника увеличивает номер, и прежние ключи просто перестают попадаться. У клиента — условные запросы: ответы справочников, рейтинга и карточки идут с `ETag` и `Cache-Control: private, no-cache`, файлы вложений и готовых отчётов — с `ETag` и `private, max-age=86400, immutable`; повтор с `If-None-Match` отвечает `304` без тела. Недоступный Redis означает «в кэше ничего нет», а не ошибку | FR-13 «кэш действий пользователя»: повторное открытие карточки и списков не должно стоить ни запроса к базе, ни лишнего трафика. `private` и обязательная проверка на сервере не дают показать данные, которые пользователь больше не вправе видеть, а хэш файла — готовый и точный ETag |
| ADR-023 | Обучающиеся и преподаватели — список у записи (`participant`), а не отдельный справочник людей. ФИО видит тот, кто видит запись; почта хранится зашифрованной, в списке показана сокращённо, а целиком отдаётся отдельным методом с записью в аудит. Список ведётся руками и файлом (JSON, CSV, XLSX, XLS), человек находится по HMAC-отпечатку почты, а без почты — по ФИО и роли | Уточнение жюри 17.09: нужны списки обучающихся и преподавателей с ФИО и email. Общий справочник людей — это отдельная база персональных данных без владельца; список у записи живёт ровно столько, сколько идёт обучение, и удаляется вместе с ним. Отпечаток нужен потому, что Fernet недетерминирован: искать по зашифрованному полю нельзя (152-ФЗ, ADR-010) |

## 2. Компоненты

| Сервис | Технология | Назначение |
|---|---|---|
| `web` | nginx | Отдаёт SPA, проксирует `/api` и `/auth`, TLS на стенде |
| `api` | FastAPI + uvicorn | REST `/api/v1`, SSE `/api/v1/events`, Swagger UI `/api/docs` |
| `worker` | arq | Отчёты, импорт, синхронизация LMS и сайта, пересчёт радара и рейтинга, подсказки норм |
| `postgres` | PostgreSQL 16+ | Доменные данные, история, витрины |
| `minio` | MinIO (S3) | Файлы вложений и отчётов отдельно от базы |
| `redis` | Redis 7 | Очередь, кэш готовых ответов справочников и рейтинга (ADR-022), поток событий |
| `keycloak` | Keycloak 26+ | Вход OIDC, роли, политики паролей и сессий |
| `mock-lms`, `mock-site` | FastAPI | Данные LMS и заявки сайта по контракту, пока нет доступа заказчика |
| `mock-messengers` | FastAPI | Заглушка Telegram Bot API и Bot API Max: принимает уведомления и показывает полученное |
| `mailpit` | Mailpit | Почтовый сервер для писем-уведомлений на стенде, просмотр писем в браузере |

Вложения и отчёты хранятся через слой `Storage`: MinIO на стенде и в compose, любое S3-совместимое хранилище в облаке, каталог на диске — для разработки без контейнеров (ADR-017).

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
3. **Импорт xls, xlsx и csv.** Загрузка (кодировка CSV определяется или задаётся) → маппинг колонок → предпросмотр → применение: каталоги, договоры и взаимодействия; даты подписания и срока лицензии пишутся в историю → пересчёт радара.
4. **Интеграции, входящие.** Воркер по расписанию получает JSON из LMS (Moodle Web Services, СЭО 3KL) и сайта → месячные метрики → заявка сопоставляется с взаимодействием по (вуз, программа, продукт) или создаёт новое на первом этапе.
5. **Интеграции, исходящие.** Изменение записи (создание, переход, смена ответственного, документ, импорт, заявка с сайта, изменение процесса) в своей транзакции пишет отметку в `integration_outbox` → воркер раз в минуту строит документы `radar-vuzov/interaction@1` и отправляет их пакетом в LMS и CMS → принятые помечаются отправленными, отклонённые по содержанию ждут человека, при недоступности получателя — повтор через 1, 5, 15, 60 минут.

## 3. Модель данных (PostgreSQL)

Конвенции: PK `id uuid`; `created_at`, `updated_at` — `timestamptz` в UTC; у каталогов мягкое удаление `archived_at`; перечисления — `text` + `CHECK`; внешние ключи `ON DELETE RESTRICT`. База создаётся с локалью UTF-8 — в локали `C` поиск без учёта регистра не работает для кириллицы. Нотация: `поле → таблица` — внешний ключ.

### Каталоги

```text
counterparty_group id, code UNIQUE, name UNIQUE, description, workflow_template_id → workflow_template,
                   position, archived_at                  -- вузы (B2B), частные лица (B2C) и новые группы
client            id, kind (person|organization), name, inn UNIQUE WHERE inn IS NOT NULL, city,
                   email_enc, phone_enc, created_by → app_user, archived_at          -- ПДн людей
university        id, name UNIQUE, short_name, region, city, is_priority2030, archived_at
direction         id, code UNIQUE, name
program           id, direction_id → direction, name, lms_course_ref, priority (0–100, ручной)
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

- Переход по умолчанию — на следующий этап; с «Обмена документами» можно сразу на «Подписание», минуя доработку. У каждого перехода вперёд есть возврат на шаг назад: комментарий обязателен, документ — нет. Комментарий обязателен для каждого перехода.
- Обязательные документы: «Подписание» — подписанный договор, «Передача материалов» — акт передачи, «Обучение преподавателей» — подтверждение обучения. Требование действует на выход вперёд; возврат назад документа не требует.
- Процесс у группы один (ADR-014). Переименование этапа применяется сразу и доступно только администратору. Добавление, удаление и перестановка этапов готовятся черновиком; при публикации все открытые записи переходят на новую схему. Запись с удалённого этапа переходит на ближайший предыдущий этап прежней схемы, который остался, а если такого нет — на ближайший следующий; `migration_map` задаёт этап явно. Если дошли до другого этапа, дни на этапе считаются заново. Черновик, который переименовывает этапы, публикует только администратор.

### Взаимодействия

```text
contract           id, university_id → university, number, signed_at, license_signed_at, license_valid_until,
                   license_term_years, transfer_status, UNIQUE(university_id, number)
interaction        id, group_id → counterparty_group, university_id | client_id (ровно один), program_id,
                   product_id (может быть пуст), contract_id → contract, workflow_version_id,
                   current_stage_id → stage, stage_entered_at, owner_user_id → app_user,
                   status (active|paused|completed|cancelled), source (manual|import|site|lms|demo),
                   version, last_activity_at,
                   UNIQUE NULLS NOT DISTINCT (university_id, program_id, product_id) WHERE status <> 'cancelled',
                   UNIQUE NULLS NOT DISTINCT (client_id, program_id, product_id) WHERE status <> 'cancelled'
interaction_contact PK(interaction_id, contact_person_id), role
transition         id, interaction_id, from_stage_id, to_stage_id, occurred_at, actor_user_id, comment,
                   source (manual|bulk|import|integration|migration)        -- только INSERT
interaction_note   id, interaction_id, author_user_id, text
attachment         id, interaction_id, transition_id, stage_id, document_type, file_name, mime_type,
                   size_bytes, sha256, storage_key, uploaded_by
assignment_change  id, interaction_id, from_user_id, to_user_id, changed_by, changed_at, reason
```

- Группа определяет процесс: запись встаёт на первый этап действующей схемы процесса своей группы, нормы и радар берутся из того же шаблона. Процесс группы с открытыми записями не заменяется — его меняют в редакторе, и записи переходят на новую схему (ADR-014).
- Процесс «Частные лица (B2C)»: заявка → консультация → договор-оферта → оплата → зачисление в LMS → обучение → итоговая аттестация → завершено. Выход с оферты, оплаты и аттестации требует документа (подписанная оферта, подтверждение оплаты, сертификат).
- Статус взаимодействия: рабочее состояние — `active`. `completed` и `paused` ставит человек через администрирование; переход на финальный этап сам по себе ничего не завершает.

### Импорт, интеграции, аналитика, аудит

```text
import_profile     id, name, file_kind (xls|xlsx|csv), column_map jsonb
import_batch       id, profile_id, file_name, file_kind, encoding, delimiter, status (uploaded|previewed|applied|failed),
                   headers jsonb, column_map jsonb, stats jsonb, uploaded_by, applied_at
import_row         id, batch_id, row_no, raw jsonb, resolution (new|update|conflict|skip|needs_program),
                   detail   -- причина, по которой строка требует внимания
integration_source id, kind (lms|site), base_url, secret_ref, is_mock, schedule_cron, last_sync_at,
                   push_enabled, last_push_at
sync_run           id, source_id, direction (pull|push), started_at, finished_at, status, stats jsonb, error_code
integration_outbox id, source_id, interaction_id, reason, status (pending|sent|failed), change_seq, locked_until,
                   attempts, next_attempt_at, last_error, sent_at,
                   UNIQUE(source_id, interaction_id) WHERE status = 'pending'
site_application   id, external_id UNIQUE, university_id, program_id, received_at, match_status, interaction_id
participant        id, interaction_id → interaction, role (student|teacher), full_name,
                   email_enc, email_fp (HMAC для поиска дублей), external_ref, source (manual|import|lms),
                   created_by, archived_at, UNIQUE(interaction_id, email_fp) WHERE email_fp IS NOT NULL
program_metric     id, university_id, program_id, period_month, metric (applications|students|streams), value, source
radar_signal       id, interaction_id, kind, severity (low|medium|high), detected_at, resolved_at, evidence jsonb,
                   UNIQUE(interaction_id, kind) WHERE resolved_at IS NULL
rating_weight_set  id, name, w_applications, w_students, w_streams, is_default   -- сумма весов 100
report_job         id, requested_by, params jsonb, status, progress, file_key, error_code
saved_view         id, user_id, page, name, filters jsonb, columns jsonb
data_access_rule   id, subject_user_id | subject_role, effect (allow|deny), scope_kind (university|direction|program|group), scope_id
audit_log          id bigserial, occurred_at, actor_user_id, action, entity_kind, entity_id, before, after, trace_id  -- только INSERT
app_setting        key, value jsonb                    -- radar_thresholds, stalled_escalation
notification       id, user_id → app_user, kind (stalled_interaction|stage_changed|workflow_changed|channel_test),
                   title, body, interaction_id, payload jsonb, dedupe_key UNIQUE, created_at, read_at
notification_channel  kind PK (telegram|max|email), name, is_enabled, is_mock, settings jsonb, secret_ref, kinds text[]
notification_address  PK(user_id, channel_kind), address, is_enabled    -- чат, пользователь Max, email
notification_delivery id, notification_id, channel_kind, status (pending|sent|failed), attempts,
                   next_attempt_at, locked_until, last_error, sent_at
```

Поля xlsx заказчика → модель: «Название ВУЗа» → `university`; «Вендор», «ПО» → `vendor`, `product`; «Номер договора», «Подписание лицензии», «Срок действия лицензии» → `contract`; «Статус по передаче» → `contract.transfer_status` и этап по карте значений; «ФИО Менеджера» → `interaction.owner_user_id`; «Ответственные от ВУЗа» → `contact_person`; «Комментарий» → `interaction_note`.

## 4. Доступ и роли

| Роль | Видит взаимодействия | Может сверх просмотра |
|---|---|---|
| `kam` — КАМ | свои (`owner_user_id` = пользователь) | переходы, комментарии, файлы в своих взаимодействиях |
| `manager` — руководитель | своей команды и свои | назначать и снимать ответственных, веса рейтинга, импорт, изменение workflow без переименования этапов |
| `admin` — администратор | все | пользователи, правила доступа к данным, интеграции, настройки, аудит, переименование этапов |

- Keycloak: realm `radar-vuzov`, публичный клиент `radar-web` (Authorization Code + PKCE), аудитория API `radar-api`, роли в claim `realm_access.roles`.
- При первом входе пользователь создаётся в `app_user` по `sub` и email из токена; роль берётся из токена, команда — из БД.
- Область видимости применяет сервисный слой ко всем запросам; запись вне области — `404 NOT_FOUND`.
- Правила доступа администратора адресуют вуз, направление, программу или группу контрагентов: так команда B2B не видит частных лиц, а команда B2C — вузы.
- Страницы и доступ к разделам по ролям — [`docs/FRONTEND_PAGES.md`](docs/FRONTEND_PAGES.md).

## 5. API

- Префикс `/api/v1`, JSON, даты ISO 8601 в UTC. Swagger UI — `/api/docs`, схема — `/api/openapi.json`, копия — `contracts/openapi.yaml`.
- Списки: `?page=1&page_size=50` (максимум 200) → `{items, total, page, page_size}`. Одинаковые фильтры у списков, отчётов и JSON-выгрузки: `period_from`, `period_to`, `university_id`, `direction_id`, `program_id`, `product_id`, `owner_id`, `stage_code`, `search` (повторяемые параметры для множественного выбора). Взаимодействие попадает в период, если создано не позже `period_to` и либо всё ещё активно, либо в периоде был хотя бы один переход. Даты сравниваются в UTC.
- Авторизация: `Authorization: Bearer <access_token>`.

### Методы v0

| Метод | Назначение |
|---|---|
| `GET /api/health` | Состояние сервиса и БД |
| `GET /api/v1/me` | Профиль: id, ФИО, роль, команда, область видимости |
| `GET /api/v1/universities`, `/{id}` | Вузы со счётчиками взаимодействий и открытых сигналов |
| `GET /api/v1/directions`, `/programs`, `/products`, `/users` | Справочники |
| `PUT /api/v1/programs/{id}/priority` | Ручной приоритет курса (0–100); меняют руководитель и админ |
| `GET /api/v1/counterparty-groups` | Группы контрагентов и их процессы |
| `GET`, `POST /api/v1/clients`, `GET /api/v1/clients/{id}` | Клиенты вне вузов; организации видны всем, люди — тем, кто с ними работает; просмотр карточки человека пишется в аудит |
| `GET /api/v1/workflows` | Процессы: действующая схема, черновик изменений, группы |
| `GET /api/v1/workflows/{template_id}`, `/norms`, `PUT /norms/{stage_code}`, `POST /norms/{stage_code}/accept-suggestion` | Схема и нормы процесса любой группы |
| `GET /api/v1/workflows/default` | Опубликованная версия базового workflow с этапами и правилами |
| `POST /api/v1/workflows` | Новый шаблон процесса |
| `POST /api/v1/workflows/{template_id}/versions` | Черновик версии копией последней |
| `PATCH /api/v1/workflow-versions/{id}` | Этапы, порядок, нормы и правила черновика |
| `PATCH /api/v1/stages/{id}` | Переименование этапа в действующей схеме — только администратор |
| `POST /api/v1/workflow-versions/{id}/publish-preview` | Предпросмотр публикации для окна подтверждения: переименования, удалённые этапы, куда и сколько записей переедет |
| `POST /api/v1/workflow-versions/{id}/publish` | Публикация: все открытые записи переходят на новую схему, с удалённых этапов — на соседний |
| `GET /api/v1/interactions` | Взаимодействия с фильтрами: группа, клиент, вуз, программа, продукт, КАМ, этап, дни на этапе, версия, открытые сигналы |
| `POST /api/v1/interactions` | Запись вручную: группа, вуз или клиент, программа, продукт, ответственный; встаёт на первый этап процесса группы |
| `GET /api/v1/interactions/{id}` | Карточка: договор, история, допустимые переходы с требованиями, сигналы |
| `POST /api/v1/interactions/{id}/transitions` | Переход: `to_stage_id`, `comment`, `expected_version`, `attachment_ids` |
| `PUT /api/v1/interactions/{id}/status` | Состояние записи: `status`, `reason`, `expected_version` — пауза, завершение, отмена, возврат в работу |
| `GET`, `POST /api/v1/interactions/{id}/notes` | Заметки по записи; заметка снимает сигнал о простое |
| `POST /api/v1/interactions/bulk-transitions` | Групповой переход: `interaction_ids`, `to_stage_code`, `comment` |
| `PUT /api/v1/interactions/{id}/owner` | Смена ответственного: `owner_id`, `reason`, `expected_version` |
| `POST /api/v1/interactions/bulk-owner` | Групповая передача записей другому КАМу |
| `POST /api/v1/interactions/{id}/attachments` | Загрузка документа (multipart: `file`, `document_type`) |
| `GET /api/v1/interactions/{id}/attachments` | Документы взаимодействия |
| `GET`, `POST /api/v1/interactions/{id}/participants` | Обучающиеся и преподаватели записи; почта в списке сокращена |
| `GET /api/v1/participants/{id}/contact` | Почта участника целиком; просмотр пишется в аудит |
| `DELETE /api/v1/participants/{id}` | Убрать участника: строка уходит, почта стирается |
| `POST /api/v1/interactions/{id}/participants/import` | Список файлом с предпросмотром |
| `GET /api/v1/interactions/{id}/participants/export` | Список файлом: JSON, CSV или XLSX |
| `GET /api/v1/attachments/{id}/file` | Файл вложения с исходным именем |
| `POST /api/v1/imports` | Загрузка выгрузки xls, xlsx или csv: колонки, подсказка соответствия, определённые кодировка и разделитель; `encoding` — указать вручную |
| `PUT /api/v1/imports/{id}/mapping` | Соответствие колонок и предпросмотр по строкам |
| `POST /api/v1/imports/{id}/apply` | Применение загрузки |
| `GET /api/v1/import-profiles` | Сохранённые соответствия колонок |
| `GET /api/v1/signals` | Открытые сигналы радара с доказательствами |
| `GET /api/v1/signals/summary` | Матрица «КАМ × вид сигнала» для тепловой карты |
| `POST /api/v1/reports` | Заказать отчёт: период, фильтры списка, колонки, формат xlsx, xls, csv (UTF-8 с BOM или windows-1251), pdf или json |
| `GET /api/v1/reports`, `/{id}` | Свои задания и состояние с прогрессом |
| `GET /api/v1/reports/{id}/file` | Готовый файл отчёта |
| `GET /api/v1/integrations` | Источники LMS и сайта |
| `POST /api/v1/integrations/{id}/sync` | Ручная синхронизация источника |
| `GET /api/v1/integrations/{id}/runs` | Журнал обмена в обе стороны (`direction`: pull, push) с кодами ошибок |
| `POST /api/v1/integrations/{id}/push`, `GET /{id}/outbox` | Отправить изменения сейчас; очередь отправки получателю |
| `PATCH /api/v1/integrations/{id}` | Включить или выключить отправку изменений источнику (администратор) |
| `GET /api/v1/interactions/{id}/export` | Документ обмена `radar-vuzov/interaction@1` по записи |
| `GET /api/v1/exchange/interactions` | Выгрузка документов обмена, `updated_since` — только изменённые |
| `GET /api/v1/site-applications` | Заявки с сайта; `match_status=unmatched` — очередь на разбор |
| `POST /api/v1/site-applications/{id}/match` | Привязать заявку к взаимодействию |
| `GET /api/v1/analytics/rating` | Рейтинг: место, балл, вклад каждой метрики, полнота данных, ручной приоритет; `order=priority` — порядок продвижения |
| `GET`, `PUT /api/v1/analytics/rating/weights` | Веса по умолчанию; меняют руководитель и админ |
| `GET /api/v1/analytics/stats/funnel`, `/stage-durations`, `/distribution` | Статистика с настройками ECharts |
| `GET`, `PATCH /api/v1/admin/users` | Сотрудники: роль, команда, доступ |
| `GET`, `POST /api/v1/admin/teams` | Команды |
| `GET`, `POST`, `DELETE /api/v1/admin/access-rules` | Правила доступа к данным |
| `GET`, `PUT /api/v1/admin/settings` | Настройки приложения |
| `GET /api/v1/admin/audit` | Журнал аудита с фильтрами |
| `POST /api/v1/admin/catalogs/{kind}`, `/{id}/archive` | Каталоги: добавление и архивирование |
| `POST /api/v1/admin/catalogs/{kind}/import` | Справочник файлом JSON, CSV, XLSX или XLS: предпросмотр (`dry_run`) и применение с итогом по каждой строке |
| `GET /api/v1/admin/catalogs/{kind}/export` | Выгрузка справочника в JSON, CSV или XLSX в том виде, в каком его принимает загрузка |
| `POST`, `PATCH /api/v1/admin/counterparty-groups`, `POST /{id}/archive` | Группы контрагентов: добавление, процесс группы, архив без открытых записей |
| `GET`, `POST /api/v1/universities/{id}/contacts` | Контакты вуза; просмотр пишется в аудит |
| `GET /api/v1/events` | Поток событий `text/event-stream` |
| `GET /api/v1/notifications`, `POST /{id}/read`, `POST /read-all` | Лента уведомлений сотрудника |
| `GET`, `PUT /api/v1/me/notification-addresses/{channel_kind}` | Свой адрес в Telegram, Max или почте |
| `GET`, `PATCH /api/v1/admin/notification-channels/{kind}`, `POST /{kind}/test` | Каналы уведомлений и пробное сообщение |
| `GET /api/v1/admin/notification-deliveries` | Журнал доставки |
| `POST /api/v1/admin/escalations/run` | Проверить зависшие записи сейчас, не дожидаясь ночи |
| `GET /api/v1/workflows/default/norms` | Нормы этапов с подсказками по истории |
| `PUT /api/v1/workflows/default/norms/{stage_code}` | Норма вручную |
| `POST /api/v1/workflows/default/norms/{stage_code}/accept-suggestion` | Принять подсказку |

Вложения лежат за интерфейсом `Storage` (`app/core/storage.py`): на стенде и в compose это MinIO (`STORAGE_BACKEND=s3`, бакет `radar-vuzov`), без контейнеров — каталог `UPLOAD_DIR`; ключ одинаковый: `interactions/{interaction_id}/{attachment_id}`. Отсутствующий объект S3 выглядит для сервисов как отсутствующий файл и превращается в `NOT_FOUND`. Тип файла проверяется дважды — по расширению и по сигнатуре содержимого, поэтому exe с именем `.pdf` отклоняется кодом `FILE_TYPE_NOT_ALLOWED`; предел размера задаёт `MAX_UPLOAD_MB` (по ТЗ 25 МБ), превышение — `FILE_TOO_LARGE`. Документ привязывается к этапу, на котором загружен, и закрывает сигнал «нет документа»; выход с этапов «Подписание», «Передача материалов» и «Обучение преподавателей» без документа недоступен.

Интеграции спрятаны за интерфейсами `LmsClient`, `SiteClient` и `InteractionReceiver` (`app/modules/integrations/clients.py`), поэтому код не зависит от того, отвечает ли настоящая Moodle или мок из `backend/mocks/`. Обмен двусторонний (ADR-018): очередь захватывается арендой (`locked_until`), а не блокировкой на время сетевого вызова, и отправка засчитывается, только если счётчик изменений записи `change_seq` не поменялся — изменение, сделанное во время отправки, уйдёт следующим пакетом. Изменения записей CRM уходят обоим получателям документом `radar-vuzov/interaction@1` (`app/modules/exchange/`) — статус и этап, ответственный, группа, контрагент, программа, продукт, договор, файлы с ключами хранилища (`backend`, `bucket`, `key`, `sha256`) и заявки сайта с их номерами; `record.version` позволяет получателю отбросить устаревший документ. Контракт приёма — `POST /api/crm/interactions` с `{items}` и ответ `{accepted, rejected}`; заглушки LMS и сайта его реализуют и показывают полученное на `GET /api/crm/interactions`. LMS даёт обучающихся и потоки, сайт — заявки и их количество за месяц; метрика обновляется по ключу «вуз, программа, месяц, метрика, источник», так что повторная синхронизация не задваивает данные, а источники не затирают друг друга. Заявка с сайта привязывается к взаимодействию по вузу, программе и продукту по умолчанию; если связки ещё нет, взаимодействие заводится на первом этапе у КАМа этого вуза, а при его отсутствии — у руководителя; если вуз или программа не нашлись в справочниках, заявка остаётся в очереди несопоставленных и ждёт человека. Каждый запуск пишется в `sync_run`: недоступный источник получает статус `failed` с кодом `INTEGRATION_UNAVAILABLE`, а остальные источники синхронизируются как обычно.

События идут в поток Redis с ограничением длины (`app/core/events.py`): `interaction.created`, `interaction.transitioned`, `signal.opened`, `signal.resolved`, `import.applied`, `report.updated`, `notification.created`. Уведомление — личное событие: его получает только адресат, даже администратор его не видит. Клиент читает их по `GET /api/v1/events` и получает только события своей области видимости — у каждого события есть владелец записи. Заголовок `Last-Event-ID` продолжает чтение с места обрыва, раз в 15 секунд приходит комментарий-пульс. Без Redis (тесты, запуск одной командой) та же логика работает в памяти процесса, поэтому поведение потока проверяется тестами без внешних служб. Ночные задачи выполняет воркер arq (`app/worker.py`): в 03:00 МСК полный пересчёт сигналов, в 03:10 — эскалация зависших записей, следом — подсказки норм по завершённым этапам (медиана и 80-й перцентиль, не меньше пяти наблюдений). Раз в минуту воркер отправляет созревшие уведомления в каналы.

Уведомления (`app/modules/notifications/`) всегда появляются в ленте сотрудника, а в Telegram, Max или почту уходят, если канал включён администратором, пересылает этот вид уведомлений и сотрудник указал свой адрес. Во внешний канал идут только заголовок события и ссылка: подробности — за входом в систему. Очередь доставки работает как у обмена — захват арендой, отправка вне транзакции и фиксация каждой доставки отдельно, поэтому один неотвечающий канал не откатывает остальные. Владелец записи узнаёт о переходе, который сделал не он (руководитель, групповой переход), и о переносе своих записей при изменении процесса. Запись без изменений дольше срока из настройки `stalled_escalation` (по умолчанию 14 дней) уведомляет руководителя команды КАМа, а если его нет или запись ведёт он сам — администраторов; один эпизод простоя даёт одно уведомление.

Групповые методы отвечают 200 со списком итогов по каждой записи — успех с новой версией или код ошибки из каталога, поэтому частичный успех считается обычным ответом. `expected_version` они не принимают: одновременные изменения отсекает блокировка строки, групповой переход разрешён только с этапов с `bulk_allowed`, а переход с требованием документа выполняется из карточки.

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

Ответы с ошибками объявлены в контракте с типом `application/problem+json`, и у каждого метода перечислены все коды, которые он может вернуть.

### Каталог кодов ошибок

| Код | HTTP | Когда |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Неверные параметры запроса; подробности в `errors` |
| `AUTH_REQUIRED` | 401 | Нет токена или он просрочен |
| `AUTH_FORBIDDEN` | 403 | Роль не позволяет действие |
| `NOT_FOUND` | 404 | Записи нет или она вне области видимости |
| `INTERACTION_VERSION_CONFLICT` | 409 | Запись уже изменил другой пользователь |
| `INTERACTION_DUPLICATE` | 409 | С этим контрагентом по той же программе и продукту запись уже ведётся. Сознательное исключение из ADR-007: без него дубль просто не дал бы завести запись, и причина осталась бы непонятной. Ни владельца, ни идентификатор чужой записи ответ не раскрывает |
| `WF_TRANSITION_NOT_ALLOWED` | 409 | Переход в выбранный этап не разрешён правилами |
| `WF_COMMENT_REQUIRED` | 422 | Для перехода нужен комментарий |
| `WF_ATTACHMENT_REQUIRED` | 422 | Для перехода нужен документ |
| `WF_VERSION_NOT_DRAFT` | 409 | В опубликованной версии разрешено только переименование |
| `WF_MIGRATION_MAP_INCOMPLETE` | 422 | Карта переноса ведёт на этап, которого нет в новой схеме |
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
| `missing_document` | этап требует документ, файла нужного типа нет и прошла половина нормы этапа | medium |
| `inactivity` | нет переходов, заметок и файлов | low — от 14 дней, medium — от 28 |

- У сигнала есть `evidence`: этап, дни, норма и её источник, дата лицензии или последнего действия — всё, чтобы эксперт пересчитал вручную.
- Пороги лицензии и простоя задаёт администратор в настройке `radar_thresholds`; пока её не сохраняли, действуют значения из таблицы. Новые пороги применяются сразу ко всем активным записям.
- Пересчёт — сразу по событию (переход, файл, договор, импорт) и раз в сутки для всех. Исправленное условие закрывает сигнал (`resolved_at`).
- Документ обязателен для выхода с этапа: правило перехода требует вложение нужного типа. После перехода сигнал закрывается, а документ остаётся в карточке этапа.
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
