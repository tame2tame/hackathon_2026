# Диаграммы «Радара вузов»

Три диаграммы, которые просило жюри: связи системы, программно-аппаратная архитектура и база
данных. Исходники — Mermaid прямо в этом файле, GitHub рисует их сам. Полная модель в ArchiMate
лежит рядом: [`model.xml`](model.xml), открывается в Archi (File → Import → Model from Open
Exchange File).

Пояснения к решениям — в [`ARCHITECTURE.md`](../../ARCHITECTURE.md), расчёты — в
[`DATA_PROCESSING.md`](../DATA_PROCESSING.md).

Те же диаграммы отрисованы в картинки — [`images/`](images): они идут в сопроводительный PDF
и в презентацию, где Mermaid не нарисуешь. Пересобрать после правки исходников:
`make docs-pdf` вставит свежие файлы, а сами картинки снимаются headless-браузером: страница
с диаграммой mermaid 11 открывается в Chrome, у отрисованного SVG берутся настоящие ширина
и высота, и снимок делается ровно под них (`--headless --window-size=W,H --screenshot`).

## 1. Диаграмма связей

Кто с кем разговаривает и по какому поводу. Стрелка — направление вызова, подпись — что передаётся.

```mermaid
flowchart LR
    kam["КАМ"]
    manager["Руководитель"]
    admin["Администратор"]

    subgraph radar["Радар вузов"]
        spa["SPA<br/>React, TanStack Query"]
        api["API<br/>FastAPI"]
        worker["Воркер<br/>arq"]
        db[("PostgreSQL<br/>данные и история")]
        cache[("Redis<br/>очередь, кэш, события")]
        files[("S3-хранилище<br/>вложения и отчёты")]
    end

    keycloak["Keycloak<br/>вход и роли"]
    lms["LMS<br/>обучающиеся, потоки"]
    site["Сайт ИТ Школы<br/>заявки"]
    messengers["Telegram и Max"]
    smtp["Почта (SMTP)"]

    kam --> spa
    manager --> spa
    admin --> spa
    spa -->|"токен OIDC"| keycloak
    spa -->|"REST /api/v1"| api
    api -->|"SSE: этапы, сигналы, отчёты"| spa
    api -->|"проверка подписи токена"| keycloak

    api --> db
    api --> cache
    api --> files
    worker --> db
    worker --> cache
    worker --> files

    lms -->|"метрики по расписанию"| worker
    site -->|"заявки по расписанию"| worker
    worker -->|"документ radar-vuzov/interaction@1"| lms
    worker -->|"тот же документ в CMS"| site
    worker -->|"уведомления"| messengers
    worker -->|"письма"| smtp
```

**Что здесь важно.** Обмен двусторонний: входящий — по расписанию, исходящий — очередью
`integration_outbox`, чтобы отказ получателя не ронял работу КАМа (ADR-018). Уведомления уходят
из воркера, а не из запроса: медленный мессенджер не должен задерживать переход по этапу
(ADR-016). Права проверяет только API — SPA лишь прячет недоступное.

## 2. Программно-аппаратная архитектура

Стенд — одна виртуальная машина в Yandex Cloud: всё поднимается `docker compose` из
[`infra/docker-compose.prod.yml`](../../infra/docker-compose.prod.yml) с дополнением
[`docker-compose.yandex.yml`](../../infra/docker-compose.yandex.yml). Файлы лежат не на машине,
а в Yandex Object Storage — облачном S3-хранилище. Наружу открыты только 80 и 443 (и 22 для
администратора). В закрытом контуре заказчика вместо Object Storage ставится MinIO или другое
S3-хранилище — код тот же, меняются адрес и ключи.

```mermaid
flowchart TB
    browser["Браузер сотрудника<br/>HTTPS"]

    subgraph cloud["Yandex Cloud"]
        subgraph server["ВМ radar — Ubuntu 24.04, Docker, 2 vCPU, 8 ГБ"]
            nginx["nginx<br/>:80, :443 → TLS Let's Encrypt, статика SPA"]

            subgraph app["Приложение"]
                api["api — uvicorn :8000<br/>образ backend"]
                worker["worker — arq<br/>тот же образ"]
            end

            subgraph state["Состояние"]
                pg["postgres:16 :5432<br/>том postgres-data"]
                redis["redis:7 :6379"]
            end

            subgraph auth["Вход"]
                kc["Keycloak 26 :8080<br/>realm radar-vuzov"]
            end

            subgraph backup["Резервные копии — том backups"]
                dump["backup — pg_dump раз в сутки"]
                offsite["backup-offsite — rclone, зашифрованные копии"]
            end

            subgraph mocks["Заглушки внешних систем"]
                mocklms["mock-lms :8100"]
                mocksite["mock-site :8101"]
                mockmsg["mock-messengers :8102"]
                mailpit["mailpit :1025, :8025"]
            end
        end

        files[("Yandex Object Storage — S3<br/>бакет файлов: вложения и отчёты, версионирование<br/>бакет копий: зашифрованные дампы")]
    end

    browser -->|":443"| nginx
    nginx -->|"/api, /events"| api
    nginx -->|"/auth"| kc
    api --> pg
    api --> redis
    api -->|"S3"| files
    worker --> pg
    worker --> redis
    worker -->|"S3"| files
    worker --> mocklms
    worker --> mocksite
    worker --> mockmsg
    worker --> mailpit
    dump --> pg
    offsite -->|"S3, бакет копий"| files
```

**Масштабирование.** Узкое место — API: он без состояния, поэтому добавляется копиями за тем же
nginx. Воркер тоже масштабируется копиями: очереди обмена и уведомлений захватываются арендой
(`locked_until`) и `SKIP LOCKED`, поэтому две копии не отправят одно и то же дважды. Тяжёлое
чтение (рейтинг, справочники) снимается кэшем в Redis (ADR-022), файлы лежат в S3 и не грузят
базу. Подробности и замеры — в [`LOAD_TEST.md`](../LOAD_TEST.md).

## 3. База данных

Главные таблицы и связи между ними. Полная модель со всеми полями — в разделе «Модель данных»
[`ARCHITECTURE.md`](../../ARCHITECTURE.md); служебные таблицы импорта, интеграций и уведомлений
здесь опущены, чтобы схема читалась.

```mermaid
erDiagram
    COUNTERPARTY_GROUP ||--o{ INTERACTION : "определяет процесс"
    COUNTERPARTY_GROUP }o--|| WORKFLOW_TEMPLATE : "идёт по"
    WORKFLOW_TEMPLATE ||--o{ WORKFLOW_VERSION : "версии схемы"
    WORKFLOW_VERSION ||--o{ STAGE : "этапы"
    STAGE ||--o{ STAGE_NORM : "норма в днях"
    STAGE ||--o{ STAGE_TRANSITION_RULE : "правила переходов"

    UNIVERSITY ||--o{ INTERACTION : "контрагент B2B"
    CLIENT ||--o{ INTERACTION : "контрагент B2C"
    DIRECTION ||--o{ PROGRAM : "включает"
    PROGRAM ||--o{ INTERACTION : "чему учим"
    PRODUCT ||--o{ INTERACTION : "на чём учим"
    APP_USER ||--o{ INTERACTION : "ответственный"
    TEAM ||--o{ APP_USER : "команда"

    INTERACTION ||--o{ TRANSITION : "история этапов"
    INTERACTION ||--o{ ATTACHMENT : "документы"
    INTERACTION ||--o{ RADAR_SIGNAL : "открытые сигналы"
    INTERACTION ||--o{ PARTICIPANT : "обучающиеся и преподаватели"
    INTERACTION ||--o{ INTERACTION_NOTE : "заметки"
    CONTRACT ||--o{ INTERACTION : "договор и лицензия"
    UNIVERSITY ||--o{ CONTRACT : "заключает"

    UNIVERSITY ||--o{ PROGRAM_METRIC : "витрина метрик"
    PROGRAM ||--o{ PROGRAM_METRIC : "по программе"

    APP_USER ||--o{ SAVED_VIEW : "свои виды списков"
    APP_USER ||--o{ NOTIFICATION : "лента уведомлений"
    APP_USER ||--o{ AUDIT_LOG : "кто что сделал"

    INTERACTION {
        uuid id PK
        uuid group_id FK
        uuid university_id FK "или client_id"
        uuid program_id FK
        uuid product_id FK "может быть пуст"
        uuid current_stage_id FK
        uuid owner_user_id FK
        string status "active paused completed cancelled"
        int version "защита от параллельных правок"
    }
    TRANSITION {
        uuid id PK
        uuid interaction_id FK
        uuid from_stage_id FK
        uuid to_stage_id FK
        timestamp occurred_at
        string comment "только INSERT, триггер запрещает UPDATE"
    }
    PARTICIPANT {
        uuid id PK
        uuid interaction_id FK
        string role "student teacher"
        string full_name
        bytea email_enc "шифрование Fernet"
        string email_fp "HMAC для поиска дублей"
    }
    RADAR_SIGNAL {
        uuid id PK
        uuid interaction_id FK
        string kind "stage_overdue license_expiring missing_document inactivity"
        string severity
        jsonb evidence "числа, по которым сигнал построен"
    }
```

**Что важно в схеме.** Контрагент у записи ровно один: либо вуз, либо клиент — условие проверяет
база (ADR-015). Частичные уникальные индексы не дают завести вторую активную запись по той же
связке «контрагент — программа — продукт». История переходов и журнал аудита только дописываются:
это обеспечивает триггер, а не договорённость.
