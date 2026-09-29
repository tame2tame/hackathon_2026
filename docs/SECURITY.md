# Безопасность: меры и где они в коде

Матрица мер по 152-ФЗ и приказу ФСТЭК России №117. Каждая строка ссылается на файл, где мера
действительно реализована: документ описывает систему, а не намерения. Что не сделано —
перечислено в конце отдельно.

## Вход и учётные записи

| Мера | Как сделано | Где |
|---|---|---|
| Пароль не короче 12 символов и не совпадает с логином | Политика realm `length(12) and notUsername` | [`infra/keycloak/realm-radar-vuzov.json`](../infra/keycloak/realm-radar-vuzov.json) |
| Блокировка после 5 неудачных попыток | `bruteForceProtected`, `failureFactor: 5`, ожидание до 15 минут | там же |
| Простой сессии 30 минут | `ssoSessionIdleTimeout: 1800`, время жизни токена 300 с | там же |
| Самостоятельная регистрация закрыта | `registrationAllowed: false` | там же |
| Вход SPA без секрета в браузере | Публичный клиент `radar-web`, Authorization Code + PKCE `S256` | там же |
| Токен проверяется по подписи, издателю и аудитории | `decode_keycloak_token` | [`backend/app/core/security.py`](../backend/app/core/security.py) |
| Режим без Keycloak запрещён в продакшене | Проверка `AUTH_MODE=dev` при `APP_ENV=production` | [`backend/app/core/config.py`](../backend/app/core/config.py) |

## Разграничение доступа

| Мера | Как сделано | Где |
|---|---|---|
| Права проверяет только сервер | Область видимости применяется в сервисном слое ко всем запросам | [`backend/app/core/scope.py`](../backend/app/core/scope.py) |
| Запись вне области не раскрывается | Ответ `404 NOT_FOUND`, а не `403` — существование чужой записи не подтверждается | [`backend/app/core/errors.py`](../backend/app/core/errors.py) |
| Правила администратора поверх ролей | `data_access_rule`: разрешение расширяет область, запрет вычитает и сильнее разрешения | [`backend/app/core/scope.py`](../backend/app/core/scope.py) |
| Действия по ролям | `require_roles` на изменении норм, импорте, интеграциях, весах рейтинга, администрировании | [`backend/app/core/security.py`](../backend/app/core/security.py) |
| Уведомления личные | Ленту и событие SSE `notification.created` видит только адресат, чужое уведомление — `404` | [`backend/app/modules/events/router.py`](../backend/app/modules/events/router.py) |
| Во внешние каналы не уходят персональные данные | В Telegram, Max и почту отправляются заголовок события и ссылка, без контрагента, ответственного и комментариев | [`backend/app/modules/notifications/service.py`](../backend/app/modules/notifications/service.py) |
| Канал ходит только по разрешённым адресам | Хост API мессенджера или почтового сервера сверяется с `NOTIFY_ALLOWED_HOSTS`; смена адреса отвязывает секрет, а пароль SMTP не уходит без STARTTLS | [`backend/app/modules/notifications/channels.py`](../backend/app/modules/notifications/channels.py) |
| Контакты клиента видит тот, кто с ним работает | Карточка организации видна всем, чтобы не плодить дубли, но email и телефон расшифровываются только создателю, его команде и владельцам записей — и каждый такой просмотр пишется в аудит | [`backend/app/modules/clients/service.py`](../backend/app/modules/clients/service.py) |
| Отчёт из очереди подчиняется правилам доступа | Воркер строит отчёт с правилами заказчика, а не с пустыми | [`backend/app/worker.py`](../backend/app/worker.py) |
| Секреты каналов уведомлений | В базе — только имя переменной, и только с префиксом `NOTIFY_`: через настройку канала нельзя отправить наружу `DATABASE_URL` или ключ шифрования | [`backend/app/modules/notifications/channels.py`](../backend/app/modules/notifications/channels.py) |

## Персональные данные

| Мера | Как сделано | Где |
|---|---|---|
| Email и телефон контактов шифруются | Fernet по ключу `PD_ENCRYPTION_KEY`; без ключа контакт с ПДн не сохраняется | [`backend/app/core/crypto.py`](../backend/app/core/crypto.py) |
| Email и телефон клиентов B2C шифруются тем же ключом | ИНН хранится только у организаций: у человека это лишние персональные данные | [`backend/app/modules/clients/service.py`](../backend/app/modules/clients/service.py) |
| Просмотр ПДн фиксируется | Записи `contact.viewed`, `client.viewed`, `participant.contact_viewed` и `participant.exported` в аудит; в журнал попадает факт, не сами данные | [`backend/app/modules/admin/service.py`](../backend/app/modules/admin/service.py) |
| Почта обучающихся и преподавателей шифруется, а в списке показана сокращённо | `и***@вуз.рф` в списке, адрес целиком — отдельным запросом с записью в аудит; рядом лежит HMAC-отпечаток, по которому загрузка файла находит дубли, но адрес из него не восстановить | [`backend/app/modules/participants/service.py`](../backend/app/modules/participants/service.py) |
| Ушедшего из группы убирают вместе с почтой | Строка уходит из списка, `email_enc` и отпечаток стираются: хранить их больше незачем | [`backend/app/modules/participants/service.py`](../backend/app/modules/participants/service.py) |
| Человека видят только те, кто с ним работает | Карточку клиента-человека видят создатель, владельцы его записей, руководитель их команды и администратор; организации видны всем, чтобы не заводить дубли | [`backend/app/modules/clients/service.py`](../backend/app/modules/clients/service.py) |
| Переписка сотрудников видна только двоим | Сообщение читают отправитель и получатель, включая администратора — чужой диалог для него пустой; ссылка на запись появляется только у того, кому запись доступна | [`backend/app/modules/messages/service.py`](../backend/app/modules/messages/service.py) |
| ПДн не попадают в логи и тексты ошибок | Ошибки отдаются кодом каталога и `trace_id`; стек — только в журнал сервера | [`backend/app/core/errors.py`](../backend/app/core/errors.py) |
| В репозитории только синтетические данные | Демо-пользователи на `example.com`, фикстуры генерируются | [`backend/app/demo.py`](../backend/app/demo.py) |

| Выгрузка не превращается в формулы | В xlsx, xls и csv значения с `=`, `+`, `-`, `@` в начале экранируются апострофом (CSV-инъекция) | [`backend/app/modules/reports/renderers.py`](../backend/app/modules/reports/renderers.py) |
| Файлы отдельно от базы | Вложения в S3-хранилище без публичного доступа (на стенде — приватный бакет Yandex Object Storage с версионированием); скачивание только через API с проверкой области видимости записи | [`backend/app/core/storage.py`](../backend/app/core/storage.py) |
| Потерявший доступ не скачает файл из кэша браузера | Вложения и отчёты отдаются с `private, no-cache` и ETag: браузер каждый раз спрашивает сервер, а тот сначала проверяет доступ; `immutable` — только у публичных картинок справки | [`backend/app/core/http_cache.py`](../backend/app/core/http_cache.py) |
| ФИО заявителя с сайта видит тот, кто видит запись | Очередь несопоставленных заявок — всем руководителям, сопоставленные — в области видимости их записи; чужую заявку не перепривязать | [`backend/app/modules/integrations/service.py`](../backend/app/modules/integrations/service.py) |
| Оплаты без лишних персональных данных | Паспорт, СНИЛС и диплом из шаблона LMS CRM не хранит — колонки пустые; в таблице оплат только номер заявки, поток и ссылки; в журнал уходят номер заявки и поток, не ФИО и не почта | [`backend/app/modules/payments/`](../backend/app/modules/payments) |
| Файл зачисления и контакты вендоров — под учётом | Выгрузка «Загрузка пользователей», просмотр и выгрузка контактов вендоров пишутся в аудит; почта и телефоны вендоров зашифрованы | [`backend/app/modules/vendors/service.py`](../backend/app/modules/vendors/service.py) |
| Персональные данные участников не хранятся вечно | Через 180 дней после завершения записи ФИО и почта участников стираются ночным заданием, в аудит пишется факт | [`backend/app/modules/participants/service.py`](../backend/app/modules/participants/service.py) |

## Журналирование и целостность

| Мера | Как сделано | Где |
|---|---|---|
| Журнал изменений со значениями до и после | `audit_log` с полями `before` и `after` | [`backend/app/modules/audit/models.py`](../backend/app/modules/audit/models.py) |
| История и аудит только дописываются | Триггеры БД запрещают `UPDATE`, `DELETE` и `TRUNCATE` и работают в режиме `ALWAYS` — их не отключает и `session_replication_role`; у роли приложения на эти таблицы нет прав `UPDATE`, `DELETE`, `TRUNCATE`; на всё есть тесты | [`backend/migrations/versions`](../backend/migrations/versions) |
| Каталоги не удаляются | Архивирование `archived_at` вместо удаления | [`backend/app/modules/admin/service.py`](../backend/app/modules/admin/service.py) |
| Параллельные изменения не затирают друг друга | `expected_version` и блокировка строки при переходах | [`backend/app/modules/interactions/service.py`](../backend/app/modules/interactions/service.py) |

## Файлы и внешние данные

| Мера | Как сделано | Где |
|---|---|---|
| Белый список типов файлов | Проверяются и расширение, и сигнатура: exe с именем `.pdf` отклоняется | [`backend/app/modules/attachments/files.py`](../backend/app/modules/attachments/files.py) |
| Предел размера загрузки | `MAX_UPLOAD_MB` (25 МБ по ТЗ), превышение — `FILE_TOO_LARGE` | [`backend/app/modules/attachments/service.py`](../backend/app/modules/attachments/service.py) |
| Имя файла обезврежено | Путь и управляющие символы вырезаются перед сохранением | [`backend/app/modules/attachments/files.py`](../backend/app/modules/attachments/files.py) |
| Ключ хранения не зависит от имени файла | `interactions/{id}/{attachment_id}`, выход за каталог хранилища проверяется | [`backend/app/core/storage.py`](../backend/app/core/storage.py) |

## Транспорт и стенд

| Мера | Как сделано | Где |
|---|---|---|
| TLS и перенаправление с 80 порта | Конфиг nginx стенда | [`infra/nginx/nginx.conf`](../infra/nginx/nginx.conf) |
| Заголовки безопасности | HSTS, `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, CSP с `frame-ancestors 'none'` | там же |
| CORS только для известных адресов | Список из `CORS_ORIGINS`, по умолчанию пусто; `*` в продакшене запрещён | [`backend/app/main.py`](../backend/app/main.py) |
| Стенд не стартует с небезопасными настройками | При `APP_ENV=production` приложение отказывается запускаться без ключа шифрования, с неверным ключом, с паролем базы из локального профиля и с `CORS_ORIGINS=*` | [`backend/app/core/config.py`](../backend/app/core/config.py) |
| Секреты только в окружении | В коде и фикстурах паролей нет; в `.env.example` — заглушки | [`backend/.env.example`](../backend/.env.example) |
| Секреты не попадают в историю | `gitleaks` в CI по всей истории | [`.github/workflows/backend.yml`](../.github/workflows/backend.yml) |
| Уязвимые зависимости | `pip-audit --strict` в CI по `requirements.lock` — ровно те версии, что ставятся в образ | там же |
| Воспроизводимая сборка | Зависимости по `backend/requirements.lock`, базовый образ и образы стенда закреплены по digest, у рабочих процессов CI только чтение репозитория | [`backend/Dockerfile`](../backend/Dockerfile), [`infra/docker-compose.prod.yml`](../infra/docker-compose.prod.yml) |

## Резервное копирование

| Мера | Как сделано | Где |
|---|---|---|
| Ежедневный дамп | Сервис `backup`: базы `radar` и `keycloak`, формат custom, хранение 14 дней на стенде | [`infra/backup/backup.sh`](../infra/backup/backup.sh) |
| Проверка восстановления | Оба дампа разворачиваются во временные базы и сверяются с рабочими | [`infra/backup/restore-check.sh`](../infra/backup/restore-check.sh) |
| Внешние копии | Шифрование открытым ключом gpg, отправка в стороннее S3; закрытый ключ вне сервера | [`infra/backup/files.sh`](../infra/backup/files.sh) |
| Ключи хранилища не видны в процессах | Конфиг `mc` во временном файле вместо аргументов | там же |
| Приложение не владеет схемой | Роль `radar_app` без DDL, история и аудит — только добавление; миграции под `radar` | [`infra/postgres/roles.sql`](../infra/postgres/roles.sql) |
| Отдельная база Keycloak | Роль `keycloak` со своим паролем, `radar_app` к ней не подключается | там же |
| Демо-пароли не уезжают на стенд | Подстановки `${DEMO_*_PASSWORD}` в realm, на стенде обязательны | [`infra/keycloak/realm-radar-vuzov.json`](../infra/keycloak/realm-radar-vuzov.json) |

Проверено 17.09 на локальном стенде: дамп 95 КБ, восстановление дало 36 таблиц, 6 взаимодействий
и 36 переходов. Заодно нашёлся дефект: у сервиса `backup` был свой `entrypoint`, из-за которого
`docker compose run backup sh /scripts/backup.sh` молча завершался нулём, ничего не сделав.

Проверено 27.09 на профиле стенда с чистого тома: `roles.sql` → `migrate` → демо-данные под
`radar_app` → API и все задания воркера под ней же. Роль приложения получает отказ на `UPDATE` и
`TRUNCATE` истории и аудита, на `ALTER TABLE ... DISABLE TRIGGER`, `DROP TABLE`,
`session_replication_role` и подключение к базе Keycloak. Дампы обеих баз восстановлены
(46 таблиц из 46, 351 взаимодействие, realm с тремя пользователями), внешние копии расшифрованы
закрытым ключом байт в байт, отправка во внешний бакет прошла.

## Что не сделано

- Сертификаты TLS на стенде не выпускались: конфиг nginx готов, но стенда пока нет (B-19).
- Политики Keycloak проверены по файлу realm и при локальном входе; на стенде не проверялись.
- Ежедневное расписание бэкапа проверено только разовым запуском: сервис в профиле `ops` с суточным циклом сутки подряд не работал.
- Аудит на уровне СУБД (`pgaudit`) не подключался: журнал ведёт приложение.
- Формальные документы по аттестации и модель угроз не составлялись — это работа за рамками кода.
