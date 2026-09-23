# Постановка: восемь «будущих разделов» интерфейса

Разделы, помеченные в меню «Скоро»: рейтинг, статистика, отчёты, команда, импорт данных, этапы
взаимодействий, каталоги, интеграции. Бэкенд под каждый готов и заморожен в
[`contracts/openapi.yaml`](../contracts/openapi.yaml); здесь — что дёргать, что показывать
и как себя вести в неудачных случаях. Типы берутся из `npm run api:generate`, поэтому имена
полей ниже совпадают с типами клиента.

## Общее для всех экранов

- **Права проверяет сервер.** Если метод вернул `403`, кнопку нужно было прятать; если `404` —
  запись вне области видимости, и это не ошибка, а «такой записи для вас нет». Роль текущего
  пользователя — в `GET /api/v1/me` (`role`: `kam`, `manager`, `admin`).
- **Ошибки** приходят как `application/problem+json`: `{code, detail, errors[], trace_id}`.
  Показывать `detail` пользователю, `code` использовать в ветвлениях, `trace_id` — в тексте
  «сообщите поддержке».
- **Списки** отдаются конвертом `{items, total, page, page_size}`; параметры `page`, `page_size`.
- **Кэш.** Справочники, рейтинг и карточка идут с `ETag`; не ставьте `cache: "no-store"`
  и не добавляйте `?_=timestamp` — иначе выключите кэш. Повторный запрос отдаст `304`,
  для `fetch` это прозрачно.
- **Живые обновления** — SSE `GET /api/v1/events`: `report.updated`, `interaction.transitioned`,
  `interaction.status_changed`, `signal.opened`, `signal.resolved`, `import.applied`,
  `notification.created`, `message.created`.
- **Сохранённые виды** (`/api/v1/saved-views`) работают на любом списке: `page` — одна из
  `interactions`, `radar`, `reports`, `rating`, `clients`; `filters` сервер не толкует
  и возвращает как есть.

## 1. Рейтинг востребованности

| Что | Метод |
|---|---|
| Таблица рейтинга | `GET /api/v1/analytics/rating` — `entity` (`program` или `university`), `period_from`, `period_to`, `direction_id` (можно несколько), `order` (`score` или `priority`), `w_applications`, `w_students`, `w_streams` |
| Веса по умолчанию | `GET`, `PUT /api/v1/analytics/rating/weights` — только руководитель и админ |
| Ручной приоритет курса | `PUT /api/v1/programs/{id}/priority`, тело `{priority: 0..100}` — руководитель и админ |

Строка (`RatingRowOut`): `place`, `place_change`, `id`, `name`, `direction_name`, `score`,
`priority`, `contributions[]`, `complete`, `missing_metrics[]`.

- Показать место, изменение места (`place_change`: `null` — «раньше не было», не рисовать
  ноль), балл и разложение по вкладам: `contributions[]` даёт `metric`, `weight`, `value`,
  `normalized`, `contribution`; их сумма равна баллу — на этом строится столбик-разложение.
- `complete: false` — пометить строку «данные неполные» и перечислить `missing_metrics`;
  прятать такие строки нельзя.
- Три ползунка весов: сумма ровно 100, иначе сервер ответит `422 VALIDATION_ERROR`. Ползунки
  меняют только текущий просмотр; «Сохранить как значения по умолчанию» — это `PUT weights`.
- Переключатель «по баллу / по приоритету»: при `order=priority` строки идут по ручному
  приоритету, но **место и балл остаются расчётными** — так и подписать, иначе выглядит
  как подтасовка.

## 2. Статистика

| Что | Метод |
|---|---|
| Воронка по этапам | `GET /api/v1/analytics/stats/funnel?group_id=` |
| Средняя длительность этапа | `GET /api/v1/analytics/stats/stage-durations?group_id=` |
| Распределение по направлениям | `GET /api/v1/analytics/stats/distribution?group_id=` |
| Те же три диаграммы файлом | `GET /api/v1/analytics/stats/report?group_id=` → PDF |

Каждый ответ (`ChartOut`) содержит `title`, `labels[]`, `values[]` и готовые настройки
`option` для ECharts — рисовать можно прямо `option`, не пересобирая данные.

- Селектор группы контрагентов вверху; без `group_id` распределение считается по всем группам,
  а воронка и длительности — по процессу группы по умолчанию (вузы).
- Кнопка «Скачать диаграммы» — тот же PDF с сервера (`Content-Disposition` уже с именем файла).
- PNG удобнее брать на клиенте: `echartsInstance.getDataURL({type: 'png', pixelRatio: 2})`.
- Пустой период — не ошибка: `values` придут нулями, показать «нет данных за период».

## 3. Отчёты

| Что | Метод |
|---|---|
| Заказать | `POST /api/v1/reports` → `202` с `ReportJobOut` |
| Список своих | `GET /api/v1/reports` |
| Состояние одного | `GET /api/v1/reports/{id}` |
| Файл | `GET /api/v1/reports/{id}/file` |

Тело заказа: `format` (`xlsx`, `xls`, `csv`, `pdf`, `json`), `encoding` (`utf-8` или
`windows-1251`, только для CSV), `period_from`, `period_to`, фильтры `group_id`,
`university_id`, `direction_id`, `program_id`, `product_id`, `owner_id`, `stage_code`,
`status`, `search` и `columns[]`.

- Отчёт строится в фоне: `status` = `queued` → `running` → `done` либо `failed`, есть `progress`
  и `row_count`. Обновлять по событию `report.updated`, а не опросом.
- `failed` приносит `error_code` — показать текст ошибки и кнопку «повторить».
- Файл отдаётся с `ETag` и суточным кэшем: повторное скачивание не тянет его заново.
  Неготовый отчёт отвечает `404` с понятным `detail` — так и показать.
- Колонки предлагать из того же списка, что принимает сервер (`columns` в контракте);
  набор фильтров тот же, что на списке взаимодействий, — их удобно переносить одним объектом.

## 4. Команда

| Что | Метод |
|---|---|
| Сотрудники в моей области | `GET /api/v1/users` |
| Все сотрудники, роль, команда, активность | `GET /api/v1/admin/users`, `PATCH /api/v1/admin/users/{id}` (`role`, `team_id`, `is_active`) — админ |
| Передача записей другому КАМу | `POST /api/v1/interactions/bulk-owner` (`interaction_ids`, `owner_id`, `reason`) |
| Точечные права | `GET`, `POST /api/v1/admin/access-rules`, `DELETE /api/v1/admin/access-rules/{id}` — админ |
| Нагрузка команды по сигналам | `GET /api/v1/signals/summary` — матрица «КАМ × вид сигнала» |

- Руководителю показывать свою команду и матрицу сигналов; кнопка «Передать записи» открывает
  выбор нового ответственного и обязательную причину.
- Передача возвращает построчный итог: часть записей может не перейти (нет прав, версия
  изменилась) — показать, что именно не удалось, а не общий отказ.
- Правило доступа: `effect` (`allow`/`deny`), `scope_kind` (`university`, `direction`,
  `program`, `group`), `scope_id`, `comment`. Запрет сильнее разрешения — подписать это
  прямо в форме.

## 5. Импорт данных

| Шаг | Метод |
|---|---|
| Загрузка файла | `POST /api/v1/imports` (multipart: `file`, необязательная `encoding`) |
| Соответствие колонок и предпросмотр | `PUT /api/v1/imports/{id}/mapping` (`column_map`, `save_as_profile`) |
| Применение | `POST /api/v1/imports/{id}/apply` |
| Сохранённые профили | `GET /api/v1/import-profiles` |

Ответ (`ImportBatchOut`): `file_name`, `file_kind`, `encoding`, `delimiter`, `status`,
`headers[]`, `column_map`, `suggested_map`, `fields[]`, `required_fields[]`, `total_rows`,
`stats`, `rows[]`.

- Мастер в три шага: файл → соответствие колонок (подставить `suggested_map`, обязательные
  поля из `required_fields`) → предпросмотр по строкам и «Применить».
- Показывать определённые `encoding` и `delimiter` с возможностью переопределить кодировку
  при повторной загрузке — это частая причина «кракозябр».
- `rows[]` в предпросмотре содержит статус каждой строки и причину ошибки: таблица с цветными
  пометками, а не один общий итог.
- Применение идемпотентно: повторный файл не создаёт дублей, в `stats` видно, сколько создано,
  обновлено и пропущено.

## 6. Этапы взаимодействий (редактор процесса)

| Что | Метод |
|---|---|
| Процессы и их группы | `GET /api/v1/workflows` |
| Схема процесса | `GET /api/v1/workflows/{template_id}` |
| Нормы этапов и подсказки | `GET /api/v1/workflows/{template_id}/norms`, `PUT .../norms/{stage_code}`, `POST .../norms/{stage_code}/accept-suggestion` |
| Черновик изменений | `POST /api/v1/workflows/{template_id}/versions`, `PATCH /api/v1/workflow-versions/{id}` (`stages`, `transitions`) |
| Предпросмотр публикации | `POST /api/v1/workflow-versions/{id}/publish-preview` |
| Публикация | `POST /api/v1/workflow-versions/{id}/publish` (`migration_map` необязательна) |
| Переименование этапа | `PATCH /api/v1/stages/{id}` (`name`) — **только админ** |

- Норма (`StageNormOut`) приходит с подсказкой: `suggested_median_days`,
  `suggested_percentile_days`, `sample_size`, `source` (`manual` или `suggested`). Показать
  подсказку рядом с полем и кнопку «Принять подсказку».
- **Окно подтверждения перед публикацией обязательно**: `publish-preview` возвращает
  `renamed[]`, `moves[]` (откуда, куда, сколько открытых записей переедет, выбран ли этап
  автоматически), `added[]`, `moved_interactions`, `requires_admin`. Если `requires_admin`
  и роль не админ — кнопку «Опубликовать» показать выключенной с объяснением.
- Карта переноса не обязательна: записи с удалённого этапа уйдут на соседний сами.
- Слово «версия» в интерфейсе не использовать — жюри просило: для пользователя это
  «изменения процесса до применения».

## 7. Каталоги

| Что | Метод |
|---|---|
| Просмотр | `GET /api/v1/universities`, `/directions`, `/programs`, `/products`, `/counterparty-groups` |
| Добавить запись | `POST /api/v1/admin/catalogs/{kind}` — админ |
| Архивировать | `POST /api/v1/admin/catalogs/{kind}/{item_id}/archive` — удаления нет |
| Загрузить файлом | `POST /api/v1/admin/catalogs/{kind}/import` (`file`, `dry_run`, `encoding`) |
| Выгрузить | `GET /api/v1/admin/catalogs/{kind}/export?format=json\|csv\|xlsx&encoding=&include_archived=` |
| Контакты вуза | `GET`, `POST /api/v1/universities/{id}/contacts`, `POST /api/v1/contacts/{id}/archive` — просмотр контактов пишется в аудит |

`kind`: `universities`, `directions`, `programs`, `vendors`, `products`, `program-products`.

- Загрузка файлом — тот же мастер, что у импорта: сначала `dry_run=true` и таблица построчного
  итога (`created`, `updated`, `unchanged`, `error` с причиной), затем «Применить».
- Выгрузка отдаёт ровно те колонки, которые принимает загрузка: «выгрузил, поправил, загрузил».
- У программы есть `priority` — поле редактируется руководителем и админом (см. экран рейтинга).
- Архивная запись не исчезает из истории: показывать её приглушённой с пометкой «в архиве».

## 8. Интеграции

| Что | Метод |
|---|---|
| Источники | `GET /api/v1/integrations` |
| Забрать данные сейчас | `POST /api/v1/integrations/{id}/sync` — руководитель и админ |
| Отправить очередь сейчас | `POST /api/v1/integrations/{id}/push` — руководитель и админ |
| Журнал запусков | `GET /api/v1/integrations/{id}/runs` |
| Очередь исходящего обмена | `GET /api/v1/integrations/{id}/outbox?status=pending\|sent\|failed` |
| Включить и выключить отправку | `PATCH /api/v1/integrations/{id}` (`push_enabled`) — админ |
| Заявки с сайта | `GET /api/v1/site-applications?match_status=unmatched`, `POST /api/v1/site-applications/{id}/match` (`interaction_id`) |

- Карточка источника: вид (`lms` или `site`), адрес, расписание, последняя синхронизация
  и последняя отправка, признак «заглушка».
- Запуск возвращает `SyncRun`: `direction` (`pull`/`push`), `status` (`done`/`failed`),
  `stats` и `error_code`. Отказ внешней системы — это `INTEGRATION_UNAVAILABLE`, и он ожидаем:
  показать спокойно, с временем следующей попытки.
- Очередь отправки: строка с причиной (`transition`, `attachment`, `status`, …), числом
  попыток и последней ошибкой. «Отправить сейчас» — та же кнопка `push`.
- Несопоставленные заявки — отдельный список с кнопкой «привязать к записи»: это ровно та
  работа, ради которой очередь и заведена.

## Порядок, если делать не всё сразу

1. **Отчёты** — единственное требование ТЗ из этого списка, у которого нет обходного пути.
2. **Рейтинг и статистика** — это «креатив и ИИ внутри» из ТЗ, самая заметная часть на показе.
3. **Импорт данных** — жюри отдельно спрашивало про загрузку файлов и кодировки.
4. **Этапы взаимодействий** — показывает, что процесс меняется без остановки работы.
5. **Каталоги, интеграции, команда** — административная часть, её можно показать и через
   Swagger, если времени не останется.

Скриншоты готовых экранов попадут во встроенную справку: снимок делается одной командой
(порядок — в [`BACKEND_PLAN.md`](BACKEND_PLAN.md), задача B-38), и руководство обновляется
`make help`.
