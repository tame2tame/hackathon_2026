# Передача фронтендеру: бэкенд после ответов жюри, 17.09.2026

Бэкенд закрыл задачи B-21 — B-27 по уточнениям жюри ([`JURY_QA.md`](JURY_QA.md)). Подробности каждой задачи и её раздел «Что меняется для фронтенда» — в [`BACKEND_PLAN.md`](BACKEND_PLAN.md). Здесь — сводка, чтобы обновить клиент за один проход. Ветка `backend/foundation`, контракт — [`contracts/openapi.yaml`](../contracts/openapi.yaml): 86 путей вместо 58.

## Как подтянуть

1. Слить `origin/backend/foundation` в свою ветку: пробное слияние с `frontend-1-s03-smoke` проходит без конфликтов, бэкенд не трогал `frontend/`.
2. `npm run api:generate` — типы из нового контракта; `npm test` покажет места, которые нужно поправить (ниже).
3. Локальная база: `make migrate` в `backend/`. Чтобы увидеть B2C, уведомления и «Ягу» в демо, базу лучше пересоздать: `make db-down`, удалить том `radar-vuzov_postgres-data`, затем `make db-up && make migrate && make seed-full`.
4. Если API запускается в compose: в нём появились `minio`, `mailpit` и `mock-messengers`. Если на хосте (`make run`) — файлы пишутся в каталог, как раньше, MinIO не нужен.

## Ломающие изменения

| Где | Было | Стало |
|---|---|---|
| `InteractionListItem`, `InteractionDetail`, ссылка на запись в сигнале (`InteractionRef`) | `university` и `product` всегда есть | `university` и `product` могут быть `null`; добавлены `group`, `counterparty`, `client`. Для подписи использовать `counterparty.short_name` (у вуза — сокращение, у клиента — имя) |
| `PATCH /api/v1/stages/{id}` | руководитель и администратор | только администратор; руководителю — 403 |
| `POST /api/v1/workflow-versions/{id}/publish` | без карты переноса — 422 `WF_MIGRATION_MAP_INCOMPLETE` | карта необязательна: записи с удалённого этапа уходят на соседний; 422 — только если карта ведёт на несуществующий этап. Черновик с переименованием публикует только администратор (403) |
| `GET /api/v1/admin/settings` | сохранённые настройки | все известные настройки с действующими значениями: добавлены `description`, `is_default`, `updated_at` бывает `null`; неизвестный ключ в `PUT` — 404 |
| `allowed_transitions` в карточке | только вперёд | есть и возвраты на шаг назад: комментарий обязателен, документ — нет |
| Сигнал простоя | с 21 и 42 дней | с 14 и 28 дней по умолчанию, пороги — настройка `radar_thresholds` |
| `GET /api/health` | `database` | ещё и `storage` |

## Новое по экранам

| Экран | Методы | Что показать |
|---|---|---|
| Все списки, канбан, радар, статистика, отчёты | фильтр `group_id`; `GET /api/v1/counterparty-groups` | переключатель «Вузы (B2B) / Частные лица (B2C)»; воронка и длительности строятся по процессу группы |
| Кнопка «Новая запись» | `POST /api/v1/interactions`; `GET`, `POST /api/v1/clients`, `GET /api/v1/clients/{id}` | сначала группа, затем вуз или клиент (человек или организация), программа, продукт; 409 `INTERACTION_DUPLICATE` — такая запись уже ведётся |
| Редактор процесса | `GET /api/v1/workflows`, `GET /api/v1/workflows/{template_id}`, нормы `/{template_id}/norms`; `POST /api/v1/workflow-versions/{id}/publish-preview` | выбор процесса группы; **окно подтверждения** перед публикацией: переименования, удалённые этапы и куда уйдут записи, `requires_admin` |
| Колокольчик и профиль | `GET /api/v1/notifications` (`unread=true&page_size=1` — число в `total`), `POST /{id}/read`, `POST /read-all`; `GET`, `PUT /api/v1/me/notification-addresses/{channel_kind}`; событие SSE `notification.created` приходит только адресату | лента уведомлений: зависшие записи, переходы, сделанные не владельцем, перенос при изменении процесса |
| Админка: уведомления | `GET`, `PATCH /api/v1/admin/notification-channels/{kind}`, `POST /{kind}/test`, `GET /api/v1/admin/notification-deliveries`, `POST /api/v1/admin/escalations/run`; настройка `stalled_escalation` | каналы Telegram, Max, почта с пробным сообщением; журнал доставки; кнопка «проверить зависшие» |
| Админка: группы | `POST`, `PATCH /api/v1/admin/counterparty-groups`, `POST /{id}/archive`; правило доступа `scope_kind: group` | — |
| Админка: каталоги | `POST /api/v1/admin/catalogs/{kind}/import` (по умолчанию `dry_run=true`), `GET /{kind}/export?format=json|csv|xlsx` | «Выгрузить» и «Загрузить файл» с предпросмотром по строкам и кнопкой «Применить» |
| Интеграции | `POST /api/v1/integrations/{id}/push`, `GET /{id}/outbox`, `PATCH /{id}` (`push_enabled`); `direction` у запусков | журнал обмена в обе стороны и очередь отправки |
| Карточка записи | `GET /api/v1/interactions/{id}/export` | ссылка «JSON для LMS/CMS» |
| Мастер импорта | `POST /api/v1/imports` принимает `.csv` и поле формы `encoding`; в ответе `encoding` и `delimiter` | показать, в какой кодировке прочитан файл, и дать перезагрузить с другой |
| Отчёты | формат `csv`, поле `encoding` (`utf-8` или `windows-1251`); колонки `group`, `counterparty` | — |

## Новые события SSE

`interaction.created` — появилась запись; `notification.created` — личное уведомление (только адресату).

## Вопросы к фронтенду

- Шрифты Rostelecom Basis в `frontend/`: репозиторий по требованию жюри станет публичным — стоит проверить, разрешает ли лицензия их распространение.
- `.github/workflows/frontend.yml` по-прежнему не запускается на изменения `contracts/**` (S-01): после этого пакета изменений это особенно заметно.
