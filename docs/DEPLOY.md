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
cp env.prod.example .env       # заполнить: пароль базы, ключ шифрования, админ Keycloak, адреса
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
docker compose -f docker-compose.prod.yml --env-file .env exec api alembic upgrade head
docker compose -f docker-compose.prod.yml --env-file .env exec api python -m scripts.seed --full
sh ../infra/smoke.sh "$PUBLIC_URL"
```

Пароли демо-входов на стенде задаются в самом Keycloak и **отличаются** от локальных из
`realm-radar-vuzov.json`: тот файл лежит в репозитории и годится только для своей машины.

## Обновление

Через GitHub Actions: рабочий процесс **Deploy**, запуск вручную (`workflow_dispatch`), с флажком
«загрузить демо-данные», если стенд поднимается заново. Он подключается по SSH, обновляет код,
пересобирает образы, прогоняет миграции и завершает проверкой [`infra/smoke.sh`](../infra/smoke.sh).

Секреты репозитория, которые для этого нужны:

| Секрет | Зачем |
|---|---|
| `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KEY` | Доступ по SSH к серверу стенда |
| `PUBLIC_URL` | Адрес стенда для smoke-проверки и ежечасного контроля |

## Контроль

- Рабочий процесс **Health** раз в час прогоняет тот же smoke-скрипт. Пока секрет `PUBLIC_URL`
  не задан, он завершается успешно с пояснением: проверять нечего.
- Бэкап делается ежедневно, хранится 14 дней; проверка восстановления —
  [`infra/backup/restore-check.sh`](../infra/backup/restore-check.sh).

## Состояние

Стенд не развёрнут: сервера и домена у команды пока нет, секреты не заводились. Всё перечисленное
подготовлено и проверено настолько, насколько это возможно без сервера — конфиг nginx проходит
`nginx -t`, бэкап и восстановление прогнаны на локальной базе, smoke-скрипт написан под адреса,
которые отдаёт этот же профиль.
