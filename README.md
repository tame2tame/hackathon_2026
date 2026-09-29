# Радар вузов

CRM контроля взаимодействия ИТ Школы Ростелекома с вузами — кейс №6 ЛЦТ 2026.

Центральная запись — **взаимодействие = контрагент × ИТ-программа × ИТ-продукт**. Оно движется по
этапам процесса (свой процесс у вузов и у частных лиц), а радар сам поднимает сигналы там, где
работа встала: затянутый этап, истекающая лицензия, нет документа, нет активности. Рядом —
рейтинг курсов по данным LMS и сайта, отчёты за период, импорт выгрузок заказчика, обмен с LMS
и CMS сайта, оплаты частных лиц с файлом зачисления в LMS, уведомления в Telegram, Max и почту.

## Стенд

**https://93-77-190-189.sslip.io** — Yandex Cloud, демо-данные: 96 вузов, около 350
взаимодействий, год истории. Вход через Keycloak: `kam.demo` (КАМ), `manager.demo`
(руководитель), `admin.demo` (администратор); пароли выдаёт команда. API и его документация —
[`/api/docs`](https://93-77-190-189.sslip.io/api/docs).

## Из чего собрано

| Часть | Где | Стек |
|---|---|---|
| Интерфейс | [`frontend/`](frontend) | React 19, Vite, TypeScript, Tailwind 4, TanStack Query |
| API и воркер | [`backend/`](backend) | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, arq |
| Инфраструктура | [`infra/`](infra) | PostgreSQL 16, Redis 7, Keycloak 26, S3 (Object Storage или MinIO), nginx |
| Контракт API | [`contracts/openapi.yaml`](contracts/openapi.yaml) | OpenAPI 3.1, генерируется из кода |
| Нагрузочный тест | [`load/`](load) | k6 |

## Запуск на своей машине

Нужны Docker, Python 3.12 и Node.js 22.

```bash
docker compose -f infra/docker-compose.yml up -d postgres redis
cd backend && make install && make migrate && make seed-full
APP_ENV=local AUTH_MODE=dev make run          # API на http://127.0.0.1:8000
```

```bash
cd frontend && npm ci
VITE_AUTH_MODE=dev npm run dev                # интерфейс на http://127.0.0.1:5173
```

В режиме `AUTH_MODE=dev` вход идёт без Keycloak — пользователь выбирается в интерфейсе; на стенде
этот режим запрещён. Проверки: `make check` в `backend/` (линтер, типы, миграции, тесты),
`npm test && npm run build` во `frontend/`.

## Документация

Одним файлом — [`docs/РадарВузов-документация.pdf`](docs/РадарВузов-документация.pdf),
презентация — [`docs/РадарВузов-презентация.pptx`](docs/РадарВузов-презентация.pptx)
([PDF](docs/РадарВузов-презентация.pdf)).

- [Архитектура и решения](ARCHITECTURE.md) — компоненты, модель данных, API, ADR
- [Соответствие ТЗ](docs/COMPLIANCE.md) — каждое требование: где сделано и чем проверено
- [Руководство пользователя](docs/USER_GUIDE.md) и [администратора](docs/ADMIN_GUIDE.md)
- [Методы обработки данных](docs/DATA_PROCESSING.md) — радар, нормы, рейтинг, импорт, оплаты
- [Меры защиты](docs/SECURITY.md) — 152-ФЗ, приказ ФСТЭК №117
- [Развёртывание](docs/DEPLOY.md), в том числе стенд в Yandex Cloud
- [Нагрузочный тест](docs/LOAD_TEST.md) и [диаграммы](docs/architecture/DIAGRAMS.md)
