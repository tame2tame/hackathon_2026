# Стенд: развёртывание и обновление

Профиль стенда — [`infra/docker-compose.prod.yml`](../infra/docker-compose.prod.yml): nginx с TLS,
API, воркер, Keycloak, PostgreSQL, Redis и ежедневный бэкап. Значений по умолчанию у секретов нет:
compose не запустится, пока переменная не задана.

## Что нужно на сервере

- Docker и плагин compose.
- Каталог `/srv/radar/hackathon_2026` с клоном репозитория.
- Сертификаты TLS (например, Let's Encrypt) — в каталоге, который указан в `CERTS_DIR`;
  внутри ожидаются `fullchain.pem` и `privkey.pem`.
- Сборка фронтенда (`npm run build`) — в каталоге из `SPA_DIR`.

## Первый запуск

```bash
cd /srv/radar/hackathon_2026/infra
cp env.prod.example .env       # заполнить: три пароля базы, ключ шифрования, Keycloak, адреса
docker compose -f docker-compose.prod.yml --env-file .env up -d postgres redis minio
docker compose -f docker-compose.prod.yml --env-file .env run --rm migrate
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
docker compose -f docker-compose.prod.yml --env-file .env run --rm api python -m scripts.seed --full
set -a && . ./.env && set +a   # PUBLIC_URL и прочее — в окружение этой оболочки
sh smoke.sh "$PUBLIC_URL"      # без адреса скрипт проверял бы 127.0.0.1:8000, а не стенд
```

Образы в профиле стенда закреплены по digest (`образ:тег@sha256:…`): тег можно перезаписать,
а стенд должен подниматься тем же, что проверяли. Зависимости Python — по
`backend/requirements.lock`, обновляются командой `make lock`.

Пароли демо-входов стенда — переменные `DEMO_KAM_PASSWORD`, `DEMO_MANAGER_PASSWORD`,
`DEMO_ADMIN_PASSWORD`: без них compose не запустится. Keycloak подставляет их в realm при первом
импорте; локальные пароли из `realm-radar-vuzov.json` на стенде не действуют.

## Роли базы

При создании пустого тома PostgreSQL выполняет [`infra/postgres/roles.sql`](../infra/postgres/roles.sql):

| Роль | Кто под ней работает | Что может |
|---|---|---|
| `radar` | сервис `migrate`, резервные копии | владелец схемы: миграции, DDL |
| `radar_app` | `api`, `worker`, загрузка демо-данных | только данные; история переходов и аудит — чтение и добавление |
| `keycloak` | Keycloak | только своя база `keycloak` |

Приложение не владеет таблицами, поэтому даже с его паролем нельзя отключить триггеры, очистить
историю или удалить таблицу. Миграции идут отдельным одноразовым сервисом `migrate` до старта API
и воркера; образ приложения сам их больше не запускает.

Если том создан до появления `roles.sql`, роли заводятся один раз вручную теми же командами из
файла (`psql -v app_password=... -v keycloak_password=...`), после чего повторно применяется
миграция `5c0d9e3a7b21`: `alembic downgrade 8a1aab17784f && alembic upgrade head` под `radar`.

## Обновление

Через GitHub Actions: рабочий процесс **Deploy**, запуск вручную (`workflow_dispatch`), с флажком
«загрузить демо-данные», если стенд поднимается заново. Он подключается по SSH, обновляет код,
собирает образы, **снимает дамп обеих баз**, прогоняет миграции сервисом `migrate`, поднимает
остальное и завершается проверкой [`infra/smoke.sh`](../infra/smoke.sh). У рабочего процесса только
право чтения репозитория.

Секреты репозитория, которые для этого нужны:

| Секрет | Зачем |
|---|---|
| `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KEY` | Доступ по SSH к серверу стенда |
| `PUBLIC_URL` | Адрес стенда для smoke-проверки и ежечасного контроля |

## Хранилище файлов

Вложения и отчёты хранятся в MinIO из того же профиля compose; логин и пароль — `MINIO_ROOT_USER`
и `MINIO_ROOT_PASSWORD` в `.env`. Бакет `radar-vuzov` создаётся при первой загрузке файла, наружу
MinIO не публикуется. Чтобы перейти на облачное S3-хранилище, достаточно поменять у `api` и `worker`
переменные `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_SECURE=true` и, если нужно,
`S3_REGION`.

## Заглушки внешних систем

На стенде LMS, сайт и мессенджеры заменены заглушками из того же образа (`mock-lms`, `mock-site`,
`mock-messengers`), а письма принимает Mailpit. Наружу они не публикуются. Посмотреть, что ушло:

- журнал доставки в админке — `GET /api/v1/admin/notification-deliveries`;
- письма — через туннель `ssh -L 8025:127.0.0.1:8025 <сервер>` и `http://127.0.0.1:8025`;
- сообщения мессенджеров — `docker compose exec api python -c "import httpx; print(httpx.get('http://mock-messengers:8102/sent').text)"`.

Когда заказчик даст настоящие адреса, меняются переменные `LMS_BASE_URL`, `SITE_BASE_URL`,
`TELEGRAM_API_URL`, `MAX_API_URL`, `SMTP_HOST`, `SMTP_PORT` и секреты `NOTIFY_*`; код не меняется.

## Контроль

- Рабочий процесс **Health** раз в час прогоняет тот же smoke-скрипт. Пока секрет `PUBLIC_URL`
  не задан, он завершается успешно с пояснением: проверять нечего.
- Бэкап делается ежедневно и хранится 14 дней: дампы **обеих** баз — `radar` и `keycloak`. Без
  второй восстановленный стенд не пустит ни одного пользователя. Проверка восстановления —
  [`infra/backup/restore-check.sh`](../infra/backup/restore-check.sh): разворачивает оба дампа во
  временные базы, сверяет число таблиц с рабочей базой, ищет realm и его пользователей.
- Файлы из MinIO копирует сервис `backup-files` — тоже ежедневно, в том же томе `backups`
  ([`infra/backup/files.sh`](../infra/backup/files.sh)). Без этой копии дамп базы бесполезен:
  вложения и готовые отчёты лежат отдельно.
- **Внешние копии.** Копия на том же сервере не спасает от потери сервера. Если задан
  `BACKUP_GPG_PUBLIC_KEY`, `backup.sh` шифрует дампы и архив файлов открытым ключом в
  `backups/offsite`, а `files.sh` отвозит их в S3-хранилище из `OFFSITE_*`. Ключ создаётся на своей
  машине (`gpg --quick-generate-key radar-backup`), на сервер кладётся только открытый
  (`infra/backup-keys/backup.asc`); закрытый хранится отдельно, иначе утечка сервера раскрывает и
  копии. Расшифровка: `gpg --decrypt radar-<дата>.dump.gpg > radar.dump`.

## Состояние

Стенд не развёрнут: сервера и домена у команды пока нет, секреты не заводились. Всё перечисленное
подготовлено и проверено настолько, насколько это возможно без сервера — конфиг nginx проходит
`nginx -t`, бэкап и восстановление прогнаны на локальной базе, копия файлов — на локальном MinIO
(семь объектов, повторный запуск ничего не перекачивает), smoke-скрипт написан под адреса,
которые отдаёт этот же профиль.
