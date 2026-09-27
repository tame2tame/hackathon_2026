// Generated from contracts/openapi.yaml. Do not edit.
export interface paths {
  "/api/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Состояние сервиса, базы данных и хранилища файлов */
    get: operations["health_api_health_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Профиль текущего пользователя */
    get: operations["read_me_api_v1_me_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/universities": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Вузы со счётчиками взаимодействий и открытых сигналов */
    get: operations["read_universities_api_v1_universities_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/universities/{university_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Вуз */
    get: operations["read_university_api_v1_universities__university_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/counterparty-groups": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Группы контрагентов
     * @description Вузы (B2B), частные лица (B2C) и группы, которые завёл администратор.
     */
    get: operations["read_groups_api_v1_counterparty_groups_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/directions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** ИТ-направления */
    get: operations["read_directions_api_v1_directions_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/programs": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** ИТ-программы */
    get: operations["read_programs_api_v1_programs_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/programs/{program_id}/priority": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /**
     * Задать приоритет курса вручную
     * @description Рейтинг востребованности считается по данным LMS и сайта, но порядок продвижения можно задать руками: приоритет показывается в справочнике и в рейтинге. Меняют руководитель и администратор, изменение пишется в аудит.
     */
    put: operations["put_program_priority_api_v1_programs__program_id__priority_put"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/products": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** ИТ-продукты */
    get: operations["read_products_api_v1_products_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/users": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Пользователи для фильтра «ответственный» */
    get: operations["read_users_api_v1_users_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/clients": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Клиенты: физические и юридические лица
     * @description Организации видны всем. Людей видит тот, кто их завёл, владельцы их записей и руководитель команды. Email и телефон в списке не показываются.
     */
    get: operations["read_clients_api_v1_clients_get"];
    put?: never;
    /**
     * Добавить клиента
     * @description Email и телефон шифруются перед записью в базу; ИНН — только у организации.
     */
    post: operations["post_client_api_v1_clients_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/clients/{client_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Карточка клиента
     * @description Просмотр карточки человека пишется в аудит: это обращение к персональным данным.
     */
    get: operations["read_client_api_v1_clients__client_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflows/default": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Опубликованная версия базового workflow */
    get: operations["read_default_workflow_api_v1_workflows_default_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflows/default/norms": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Нормы этапов с подсказками по истории */
    get: operations["read_norms_api_v1_workflows_default_norms_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflows/default/norms/{stage_code}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** Задать норму этапа вручную */
    put: operations["put_norm_api_v1_workflows_default_norms__stage_code__put"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflows/default/norms/{stage_code}/accept-suggestion": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Принять подсказку нормы
     * @description Нормой становится 80-й перцентиль завершённых этапов.
     */
    post: operations["post_accept_suggestion_api_v1_workflows_default_norms__stage_code__accept_suggestion_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflows": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Процессы и группы, которые по ним работают
     * @description У каждой группы контрагентов свой процесс; черновик изменений виден, если начат.
     */
    get: operations["read_workflows_api_v1_workflows_get"];
    put?: never;
    /** Создать шаблон процесса */
    post: operations["post_template_api_v1_workflows_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflows/{template_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Действующая схема процесса */
    get: operations["read_workflow_api_v1_workflows__template_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflows/{template_id}/norms": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Нормы этапов процесса с подсказками по истории */
    get: operations["read_template_norms_api_v1_workflows__template_id__norms_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflows/{template_id}/norms/{stage_code}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** Задать норму этапа процесса вручную */
    put: operations["put_template_norm_api_v1_workflows__template_id__norms__stage_code__put"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflows/{template_id}/norms/{stage_code}/accept-suggestion": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Принять подсказку нормы этапа процесса */
    post: operations["post_template_accept_suggestion_api_v1_workflows__template_id__norms__stage_code__accept_suggestion_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflows/{template_id}/versions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Создать черновик версии
     * @description Черновик копирует последнюю версию шаблона: править проще, чем собирать заново.
     */
    post: operations["post_version_api_v1_workflows__template_id__versions_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflow-versions/{version_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /**
     * Изменить черновик версии
     * @description Этапы, их порядок, нормы, требования к документам и правила переходов.
     */
    patch: operations["patch_workflow_version_api_v1_workflow_versions__version_id__patch"];
    trace?: never;
  };
  "/api/v1/stages/{stage_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /**
     * Переименовать этап
     * @description Единственное изменение, разрешённое в действующей схеме. Переименование статуса — чувствительная операция, поэтому доступно только администратору.
     */
    patch: operations["patch_stage_api_v1_stages__stage_id__patch"];
    trace?: never;
  };
  "/api/v1/workflow-versions/{version_id}/publish-preview": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Предпросмотр публикации
     * @description Ничего не меняет. Показывает переименованные и добавленные этапы, удалённые этапы с числом открытых записей и этапом, куда они переедут, и нужен ли администратор. Данные для окна подтверждения перед публикацией.
     */
    post: operations["post_publish_preview_api_v1_workflow_versions__version_id__publish_preview_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/workflow-versions/{version_id}/publish": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Опубликовать изменения процесса
     * @description Все открытые взаимодействия переезжают на новую схему переходом `migration`, прежняя схема становится `retired`. Записи с удалённого этапа переходят на ближайший предыдущий этап, а если его нет — на следующий; `migration_map` задаёт другой этап явно. Черновик с переименованием этапов публикует только администратор.
     */
    post: operations["post_publish_api_v1_workflow_versions__version_id__publish_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Взаимодействия с фильтрами */
    get: operations["read_interactions_api_v1_interactions_get"];
    put?: never;
    /**
     * Завести взаимодействие вручную
     * @description Запись встаёт на первый этап процесса своей группы. Контрагент — ровно один: вуз или клиент. Продуктозависимой программе нужен её продукт. Назначить другого ответственного может руководитель в пределах команды или администратор.
     */
    post: operations["post_interaction_api_v1_interactions_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/{interaction_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Карточка взаимодействия
     * @description История, допустимые переходы с требованиями и открытые сигналы. Ответ помечен ETag: открытая заново карточка достаётся из кэша браузера, если на сервере ничего не менялось.
     */
    get: operations["read_interaction_api_v1_interactions__interaction_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/{interaction_id}/transitions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Перевести взаимодействие на другой этап */
    post: operations["post_transition_api_v1_interactions__interaction_id__transitions_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/{interaction_id}/notes": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Заметки по взаимодействию */
    get: operations["read_notes_api_v1_interactions__interaction_id__notes_get"];
    put?: never;
    /**
     * Добавить заметку
     * @description Заметка считается работой по записи и снимает сигнал о простое.
     */
    post: operations["post_note_api_v1_interactions__interaction_id__notes_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/{interaction_id}/status": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /**
     * Приостановить, завершить, отменить или вернуть запись в работу
     * @description Состояние записи ставит человек: финальный этап сам по себе ничего не завершает. Для паузы и отмены нужна причина — она остаётся в аудите. Неактивная запись не даёт сигналов радара и не принимает переходы. Возврат отменённой в работу невозможен, если такую же связку уже ведёт другая запись.
     */
    put: operations["put_status_api_v1_interactions__interaction_id__status_put"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/bulk-transitions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Перевести несколько взаимодействий на один этап
     * @description Разрешён только с этапов с `bulk_allowed`. У каждой записи свой итог, поэтому частичный успех — обычный ответ. Переход с требованием документа выполняется в карточке.
     */
    post: operations["post_bulk_transitions_api_v1_interactions_bulk_transitions_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/{interaction_id}/owner": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /**
     * Сменить ответственного КАМа
     * @description Доступно руководителю в пределах команды и администратору.
     */
    put: operations["put_owner_api_v1_interactions__interaction_id__owner_put"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/bulk-owner": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Передать несколько взаимодействий другому КАМу
     * @description Итог по каждой записи; недоступные записи возвращают `NOT_FOUND`.
     */
    post: operations["post_bulk_owner_api_v1_interactions_bulk_owner_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/{interaction_id}/export": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Документ обмена по записи
     * @description JSON `radar-vuzov/interaction@1`: статус, ответственный, контрагент, программа, продукт и ключи связей с записями базы и файлами в S3. Тот же документ уходит в LMS и CMS.
     */
    get: operations["read_interaction_document_api_v1_interactions__interaction_id__export_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/exchange/interactions": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Выгрузка записей в JSON
     * @description Документы `radar-vuzov/interaction@1` в области видимости пользователя. `updated_since` отдаёт только изменённые с этого момента — так внешняя система забирает изменения по расписанию, не перечитывая всё.
     */
    get: operations["read_exchange_api_v1_exchange_interactions_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/{interaction_id}/attachments": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Документы взаимодействия */
    get: operations["read_attachments_api_v1_interactions__interaction_id__attachments_get"];
    put?: never;
    /**
     * Загрузить документ к взаимодействию
     * @description Файл проверяется по расширению и сигнатуре, лимит задаёт `MAX_UPLOAD_MB`. Документ привязывается к текущему этапу и закрывает сигнал «нет документа».
     */
    post: operations["post_attachment_api_v1_interactions__interaction_id__attachments_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/attachments/{attachment_id}/file": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Скачать файл вложения */
    get: operations["read_attachment_file_api_v1_attachments__attachment_id__file_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/imports": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Загрузить выгрузку xls, xlsx или csv
     * @description Возвращает колонки файла, подсказку соответствия по заголовкам ТЗ и параметры чтения. Кодировку CSV система определяет сама (BOM, UTF-8, иначе cp1251, KOI8-R или cp866 по содержимому), разделитель — по образцу строк. Если в предпросмотре «кракозябры», загрузите файл снова, указав `encoding`; для старых xls без кодовой страницы она тоже учитывается.
     */
    post: operations["post_import_api_v1_imports_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/imports/{batch_id}/mapping": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /**
     * Задать соответствие колонок и увидеть предпросмотр
     * @description Каждая строка получает решение: new, update, conflict, skip или needs_program.
     */
    put: operations["put_mapping_api_v1_imports__batch_id__mapping_put"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/imports/{batch_id}/apply": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Применить загрузку
     * @description Создаёт и обновляет записи по строкам new и update, затем пересчитывает радар.
     */
    post: operations["post_apply_api_v1_imports__batch_id__apply_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/import-profiles": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Сохранённые соответствия колонок */
    get: operations["read_import_profiles_api_v1_import_profiles_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/integrations": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Источники LMS и сайта */
    get: operations["read_integrations_api_v1_integrations_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/integrations/{source_id}/sync": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Синхронизировать источник вручную
     * @description Запись в журнале появляется и при отказе источника: там будет код ошибки.
     */
    post: operations["post_sync_api_v1_integrations__source_id__sync_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/integrations/{source_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** Включить или выключить отправку изменений источнику */
    patch: operations["patch_source_api_v1_integrations__source_id__patch"];
    trace?: never;
  };
  "/api/v1/integrations/{source_id}/push": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Отправить изменения записей в систему сейчас
     * @description То же, что делает воркер раз в минуту: документы `radar-vuzov/interaction@1` по записям из очереди уходят одним пакетом. Запуск пишется в журнал с направлением `push`, отказ получателя — с кодом `INTEGRATION_UNAVAILABLE` и повтором позже.
     */
    post: operations["post_push_api_v1_integrations__source_id__push_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/integrations/{source_id}/outbox": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Очередь отправки источнику
     * @description Какие записи ждут отправки, ушли или отклонены получателем и почему.
     */
    get: operations["read_outbox_api_v1_integrations__source_id__outbox_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/integrations/{source_id}/runs": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Журнал обмена с источником в обе стороны */
    get: operations["read_runs_api_v1_integrations__source_id__runs_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/site-applications": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Заявки с сайта
     * @description Без фильтра — все заявки; `match_status=unmatched` — очередь на разбор.
     */
    get: operations["read_applications_api_v1_site_applications_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/site-applications/{application_id}/match": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Привязать заявку к взаимодействию */
    post: operations["post_match_api_v1_site_applications__application_id__match_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/signals": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Открытые сигналы радара
     * @description Сначала высокая серьёзность, затем самые свежие. Учитывает область видимости.
     */
    get: operations["read_signals_api_v1_signals_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/signals/summary": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Матрица «КАМ × вид сигнала»
     * @description Тепловая карта руководителя: открытые сигналы по видам у каждого КАМа.
     */
    get: operations["read_signals_summary_api_v1_signals_summary_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/reports": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Свои задания на отчёт */
    get: operations["read_reports_api_v1_reports_get"];
    put?: never;
    /**
     * Заказать отчёт
     * @description Отчёт строится в фоне: ответ содержит id задания, дальше состояние смотрят в `GET /api/v1/reports/{id}`. Колонки: group, counterparty, university, direction, program, product, stage, owner, contract, license_valid_until, days_on_stage, signals.
     */
    post: operations["post_report_api_v1_reports_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/reports/{report_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Состояние отчёта */
    get: operations["read_report_api_v1_reports__report_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/reports/{report_id}/file": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Скачать готовый отчёт */
    get: operations["read_report_file_api_v1_reports__report_id__file_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/analytics/rating": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Рейтинг востребованности
     * @description Балл считается по заявкам, обучающимся и потокам с нормированием внутри направления. Вклад каждой метрики возвращается вместе с баллом, а неполные данные помечаются.
     */
    get: operations["read_rating_api_v1_analytics_rating_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/analytics/rating/weights": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Веса рейтинга по умолчанию */
    get: operations["read_weights_api_v1_analytics_rating_weights_get"];
    /**
     * Изменить веса рейтинга
     * @description Сумма весов — 100. Меняют руководитель и администратор.
     */
    put: operations["put_weights_api_v1_analytics_rating_weights_put"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/analytics/stats/funnel": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Воронка по этапам процесса группы */
    get: operations["read_funnel_api_v1_analytics_stats_funnel_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/analytics/stats/stage-durations": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Средняя длительность этапов процесса группы */
    get: operations["read_stage_durations_api_v1_analytics_stats_stage_durations_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/analytics/stats/report": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Статистика диаграммами в PDF
     * @description Воронка, длительности этапов и распределение по направлениям одним файлом: те же числа, что отдают методы статистики, нарисованы столбиками. Нужно там, где браузера нет — письмо вузу, распечатка на совещание.
     */
    get: operations["read_stats_report_api_v1_analytics_stats_report_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/analytics/stats/distribution": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Распределение по направлениям
     * @description Без группы — по всем группам сразу.
     */
    get: operations["read_distribution_api_v1_analytics_stats_distribution_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/users": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Сотрудники */
    get: operations["read_users_api_v1_admin_users_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/users/{user_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /** Роль, команда и доступ сотрудника */
    patch: operations["patch_user_api_v1_admin_users__user_id__patch"];
    trace?: never;
  };
  "/api/v1/admin/teams": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Команды */
    get: operations["read_teams_api_v1_admin_teams_get"];
    put?: never;
    /** Создать команду */
    post: operations["post_team_api_v1_admin_teams_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/access-rules": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Правила доступа к данным
     * @description Запрет сильнее разрешения; правила применяются поверх ролей во всех списках.
     */
    get: operations["read_rules_api_v1_admin_access_rules_get"];
    put?: never;
    /** Добавить правило доступа */
    post: operations["post_rule_api_v1_admin_access_rules_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/access-rules/{rule_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    /** Убрать правило доступа */
    delete: operations["delete_rule_api_v1_admin_access_rules__rule_id__delete"];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/settings": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Настройки приложения */
    get: operations["read_settings_api_v1_admin_settings_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/settings/{key}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /**
     * Изменить настройку
     * @description Значение проверяется схемой настройки; пропущенные поля получают значения по умолчанию. Неизвестный ключ — `NOT_FOUND`. Изменение пишется в аудит, новые пороги радара применяются сразу.
     */
    put: operations["put_setting_api_v1_admin_settings__key__put"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/audit": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Журнал аудита
     * @description Значения до и после изменения; просмотр персональных данных тоже записывается.
     */
    get: operations["read_audit_api_v1_admin_audit_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/catalogs/{kind}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Добавить запись каталога
     * @description Каталоги: universities, directions, programs, vendors, products.
     */
    post: operations["post_catalog_item_api_v1_admin_catalogs__kind__post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/catalogs/{kind}/import": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Загрузить справочник файлом
     * @description JSON (массив объектов или `{items}`), CSV, XLSX или XLS. Справочники: universities, directions, programs, vendors, products, program-products. Колонки называются как в выгрузке или по именам полей. Записи находятся по естественному ключу: повторная загрузка не создаёт дублей, пустая ячейка не стирает поле, архивная запись возвращается. По умолчанию — предпросмотр (`dry_run=true`): итог по каждой строке без изменений в базе.
     */
    post: operations["post_catalog_import_api_v1_admin_catalogs__kind__import_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/catalogs/{kind}/export": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Выгрузить справочник файлом
     * @description Те же колонки, что принимает загрузка: выгрузил, поправил, загрузил обратно. CSV — через точку с запятой, UTF-8 с BOM или windows-1251.
     */
    get: operations["read_catalog_export_api_v1_admin_catalogs__kind__export_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/catalogs/{kind}/{item_id}/archive": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Архивировать запись каталога
     * @description Удаления нет: на записи ссылаются взаимодействия и история.
     */
    post: operations["post_catalog_archive_api_v1_admin_catalogs__kind___item_id__archive_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/counterparty-groups": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Добавить группу контрагентов
     * @description Новая группа работает по уже опубликованному процессу.
     */
    post: operations["post_group_api_v1_admin_counterparty_groups_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/counterparty-groups/{group_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /**
     * Изменить группу контрагентов
     * @description Название, описание, порядок и процесс. Процесс группы с открытыми записями не заменяется: его меняют в редакторе, и записи переходят на новую схему.
     */
    patch: operations["patch_group_api_v1_admin_counterparty_groups__group_id__patch"];
    trace?: never;
  };
  "/api/v1/admin/counterparty-groups/{group_id}/archive": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Архивировать группу контрагентов
     * @description Только без открытых записей: история закрытых остаётся.
     */
    post: operations["post_group_archive_api_v1_admin_counterparty_groups__group_id__archive_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/universities/{university_id}/contacts": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Контакты вуза
     * @description Просмотр записывается в аудит: это обращение к персональным данным.
     */
    get: operations["read_contacts_api_v1_universities__university_id__contacts_get"];
    put?: never;
    /**
     * Добавить контакт вуза
     * @description Email и телефон шифруются перед записью в базу.
     */
    post: operations["post_contact_api_v1_universities__university_id__contacts_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/contacts/{contact_id}/archive": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Архивировать контакт */
    post: operations["post_contact_archive_api_v1_contacts__contact_id__archive_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/notifications": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Мои уведомления
     * @description Сначала новые. Непрочитанные — `unread=true`; их число — поле `total`.
     */
    get: operations["read_notifications_api_v1_notifications_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/notifications/read-all": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Отметить все уведомления прочитанными */
    post: operations["post_read_all_api_v1_notifications_read_all_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/notifications/{notification_id}/read": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Отметить уведомление прочитанным */
    post: operations["post_read_api_v1_notifications__notification_id__read_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/notification-addresses": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Мои адреса в каналах уведомлений
     * @description Куда приходят уведомления: чат Telegram, пользователь Max, почта.
     */
    get: operations["read_addresses_api_v1_me_notification_addresses_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/me/notification-addresses/{channel_kind}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** Задать свой адрес в канале */
    put: operations["put_address_api_v1_me_notification_addresses__channel_kind__put"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/notification-channels": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Каналы уведомлений
     * @description Telegram, Max и почта. Секреты не показываются: только имя переменной и признак.
     */
    get: operations["read_channels_api_v1_admin_notification_channels_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/notification-channels/{channel_kind}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    /**
     * Настроить канал уведомлений
     * @description Включение, адрес API или почтового сервера, виды уведомлений. Токен или пароль задаётся переменной окружения `NOTIFY_*`, в базе хранится только её имя.
     */
    patch: operations["patch_channel_api_v1_admin_notification_channels__channel_kind__patch"];
    trace?: never;
  };
  "/api/v1/admin/notification-channels/{channel_kind}/test": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Пробное сообщение в канал
     * @description Сообщение уходит самому администратору сразу, без очереди; ответ — итог доставки.
     */
    post: operations["post_channel_test_api_v1_admin_notification_channels__channel_kind__test_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/notification-deliveries": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Журнал доставки уведомлений */
    get: operations["read_deliveries_api_v1_admin_notification_deliveries_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/admin/escalations/run": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Проверить зависшие записи сейчас
     * @description То же, что ночная проверка: записи без изменений дольше срока из настройки `stalled_escalation` уведомляют руководителя команды или администраторов. Повторный запуск не дублирует уведомления.
     */
    post: operations["post_escalations_run_api_v1_admin_escalations_run_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/help": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Разделы встроенной справки
     * @description Руководство пользователя внутри продукта. Разделы отдаются по роли: то, что настраивает администратор, КАМу не показывается.
     */
    get: operations["read_topics_api_v1_help_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/help/images/{name}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Картинка из справки
     * @description Скриншоты экранов, на которые ссылаются разделы руководства.
     */
    get: operations["read_image_api_v1_help_images__name__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/help/{slug}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Раздел справки
     * @description Текст в Markdown: заголовки, списки и таблицы.
     */
    get: operations["read_topic_api_v1_help__slug__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/messages": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Мои переписки
     * @description С кем шла переписка, последнее сообщение и сколько сообщений не прочитано. Общее число непрочитанных — `unread_total`, для значка в шапке.
     */
    get: operations["read_dialogs_api_v1_messages_get"];
    put?: never;
    /**
     * Написать сотруднику
     * @description Сообщение видят только двое. Можно сослаться на свою запись: собеседник увидит ссылку, если запись доступна и ему.
     */
    post: operations["post_message_api_v1_messages_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/messages/{peer_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Переписка с сотрудником
     * @description Сначала старые сообщения. Чужую переписку не покажет: видно только свою.
     */
    get: operations["read_messages_api_v1_messages__peer_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/messages/{peer_id}/read": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Отметить переписку прочитанной */
    post: operations["post_read_api_v1_messages__peer_id__read_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/{interaction_id}/participants": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Обучающиеся и преподаватели по записи
     * @description ФИО и роль видит тот, кто видит запись. Почта показана сокращённо (и***@вуз.рф): адрес целиком отдаёт отдельный метод, и его запрос пишется в аудит.
     */
    get: operations["read_participants_api_v1_interactions__interaction_id__participants_get"];
    put?: never;
    /** Добавить обучающегося или преподавателя */
    post: operations["post_participant_api_v1_interactions__interaction_id__participants_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/participants/{participant_id}/contact": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Почта участника целиком
     * @description Персональные данные: каждый просмотр пишется в журнал аудита.
     */
    get: operations["read_participant_contact_api_v1_participants__participant_id__contact_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/participants/{participant_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    /**
     * Убрать участника из списка
     * @description Строка уходит из списка, а почта стирается: хранить её больше незачем.
     */
    delete: operations["delete_participant_api_v1_participants__participant_id__delete"];
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/{interaction_id}/participants/import": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /**
     * Загрузить список файлом
     * @description JSON, CSV, XLSX или XLS с колонками «ФИО», «Email», «Роль» и «Идентификатор в LMS». Человек находится по почте, а без почты — по ФИО и роли: повторная загрузка того же файла не создаёт дублей. По умолчанию — предпросмотр (`dry_run=true`).
     */
    post: operations["post_participants_import_api_v1_interactions__interaction_id__participants_import_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/interactions/{interaction_id}/participants/export": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Выгрузить список файлом
     * @description Те же колонки, что принимает загрузка. В файле почта целиком — выгрузка пишется в аудит.
     */
    get: operations["read_participants_export_api_v1_interactions__interaction_id__participants_export_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/saved-views": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Мои сохранённые виды
     * @description Набор фильтров и колонок под своим названием. Виды свои у каждого.
     */
    get: operations["read_views_api_v1_saved_views_get"];
    put?: never;
    /** Сохранить вид */
    post: operations["post_view_api_v1_saved_views_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/saved-views/{view_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    post?: never;
    /** Удалить сохранённый вид */
    delete: operations["remove_view_api_v1_saved_views__view_id__delete"];
    options?: never;
    head?: never;
    /**
     * Изменить сохранённый вид
     * @description Название, фильтры или колонки. Пропущенное поле остаётся как было.
     */
    patch: operations["patch_view_api_v1_saved_views__view_id__patch"];
    trace?: never;
  };
  "/api/v1/events": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /**
     * Поток событий
     * @description `text/event-stream`. Заголовок `Last-Event-ID` досылает пропущенное после обрыва связи; раз в 15 секунд приходит комментарий-пульс.
     */
    get: operations["read_events_api_v1_events_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /**
     * AccessRuleCreate
     * @description Правило адресуется либо сотруднику, либо роли — ровно одно из двух.
     */
    AccessRuleCreate: {
      /** Subject User Id */
      subject_user_id?: string | null;
      subject_role?: components["schemas"]["Role"] | null;
      /**
       * Effect
       * @enum {string}
       */
      effect: "allow" | "deny";
      /**
       * Scope Kind
       * @enum {string}
       */
      scope_kind: "university" | "direction" | "program" | "group";
      /**
       * Scope Id
       * Format: uuid
       */
      scope_id: string;
      /** Comment */
      comment?: string | null;
    };
    /** AccessRuleOut */
    AccessRuleOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Subject User Id */
      subject_user_id: string | null;
      /** Subject Role */
      subject_role: string | null;
      /** Effect */
      effect: string;
      /** Scope Kind */
      scope_kind: string;
      /**
       * Scope Id
       * Format: uuid
       */
      scope_id: string;
      /** Comment */
      comment: string | null;
    };
    /** AddressOut */
    AddressOut: {
      /**
       * Channel Kind
       * @enum {string}
       */
      channel_kind: "telegram" | "max" | "email";
      /** Channel Name */
      channel_name: string;
      /**
       * Channel Enabled
       * @description Включил ли канал администратор
       */
      channel_enabled: boolean;
      /**
       * Address
       * @description Чат Telegram, пользователь Max или email
       */
      address: string | null;
      /** Is Enabled */
      is_enabled: boolean;
    };
    /** AddressUpdate */
    AddressUpdate: {
      /** Address */
      address: string;
      /**
       * Is Enabled
       * @default true
       */
      is_enabled: boolean;
    };
    /** AdminUserOut */
    AdminUserOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Email */
      email: string;
      /** Full Name */
      full_name: string;
      role: components["schemas"]["Role"];
      /** Team Id */
      team_id: string | null;
      /** Is Active */
      is_active: boolean;
    };
    /** AdminUserUpdate */
    AdminUserUpdate: {
      role?: components["schemas"]["Role"] | null;
      /** Team Id */
      team_id?: string | null;
      /**
       * Is Active
       * @description Отключённый сотрудник не входит
       */
      is_active?: boolean | null;
    };
    /** AllowedTransitionOut */
    AllowedTransitionOut: {
      to_stage: components["schemas"]["StageRef"];
      /** Requires Comment */
      requires_comment: boolean;
      /** Requires Attachment */
      requires_attachment: boolean;
    };
    /** ApplicationMatch */
    ApplicationMatch: {
      /**
       * Interaction Id
       * Format: uuid
       * @description Взаимодействие, к которому относится заявка
       */
      interaction_id: string;
    };
    /** ApplyResult */
    ApplyResult: {
      /**
       * Batch Id
       * Format: uuid
       */
      batch_id: string;
      /** Created */
      created: number;
      /** Updated */
      updated: number;
      /** Skipped */
      skipped: number;
      /** Conflicts */
      conflicts: number;
      /** Needs Program */
      needs_program: number;
    };
    /** AttachmentOut */
    AttachmentOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** File Name */
      file_name: string;
      /** Mime Type */
      mime_type: string;
      /** Size Bytes */
      size_bytes: number;
      /**
       * Document Type
       * @description Тип документа этапа, если указан при загрузке
       */
      document_type: string | null;
      /**
       * Sha256
       * @description Контрольная сумма: видно повторную загрузку того же файла
       */
      sha256: string;
      /**
       * Stage Id
       * Format: uuid
       * @description Этап, на котором файл загружен
       */
      stage_id: string;
      /**
       * Uploaded By
       * Format: uuid
       */
      uploaded_by: string;
      /**
       * Uploaded At
       * Format: date-time
       */
      uploaded_at: string;
    };
    /** AuditEntryOut */
    AuditEntryOut: {
      /** Id */
      id: number;
      /**
       * Occurred At
       * Format: date-time
       */
      occurred_at: string;
      /** Actor User Id */
      actor_user_id: string | null;
      /** Action */
      action: string;
      /** Entity Kind */
      entity_kind: string;
      /** Entity Id */
      entity_id: string | null;
      /** Before */
      before: {
        [key: string]: unknown;
      } | null;
      /** After */
      after: {
        [key: string]: unknown;
      } | null;
      /** Trace Id */
      trace_id: string | null;
    };
    /** Body_post_attachment_api_v1_interactions__interaction_id__attachments_post */
    Body_post_attachment_api_v1_interactions__interaction_id__attachments_post: {
      /**
       * File
       * @description Файл документа
       */
      file: string;
      /**
       * Document Type
       * @description Тип документа этапа, например signed_contract
       */
      document_type?: string | null;
    };
    /** Body_post_catalog_import_api_v1_admin_catalogs__kind__import_post */
    Body_post_catalog_import_api_v1_admin_catalogs__kind__import_post: {
      /**
       * File
       * @description Файл справочника
       */
      file: string;
      /**
       * Dry Run
       * @description Только показать, что будет
       * @default true
       */
      dry_run: boolean;
      /**
       * Encoding
       * @description Кодировка CSV, если определилась неверно
       */
      encoding?:
        ("utf-8" | "windows-1251" | "koi8-r" | "cp866" | "utf-16") | null;
    };
    /** Body_post_import_api_v1_imports_post */
    Body_post_import_api_v1_imports_post: {
      /**
       * File
       * @description Книга Excel или CSV с выгрузкой
       */
      file: string;
      /**
       * Encoding
       * @description Кодировка файла, если определилась неверно
       */
      encoding?:
        ("utf-8" | "windows-1251" | "koi8-r" | "cp866" | "utf-16") | null;
    };
    /** Body_post_participants_import_api_v1_interactions__interaction_id__participants_import_post */
    Body_post_participants_import_api_v1_interactions__interaction_id__participants_import_post: {
      /**
       * File
       * @description Файл списка
       */
      file: string;
      /**
       * Dry Run
       * @description Только показать, что будет
       * @default true
       */
      dry_run: boolean;
      /**
       * Role
       * @description Роль строк без колонки «Роль»
       * @default student
       * @enum {string}
       */
      role: "student" | "teacher";
      /**
       * Encoding
       * @description Кодировка CSV, если определилась неверно
       */
      encoding?:
        ("utf-8" | "windows-1251" | "koi8-r" | "cp866" | "utf-16") | null;
    };
    /** BulkItemResult */
    BulkItemResult: {
      /**
       * Interaction Id
       * Format: uuid
       */
      interaction_id: string;
      /** Ok */
      ok: boolean;
      /**
       * Version
       * @description Новая версия записи при успехе
       */
      version?: number | null;
      /** @description Код ошибки из каталога при отказе */
      code?: components["schemas"]["ErrorCode"] | null;
      /** Detail */
      detail?: string | null;
    };
    /** BulkOwnerRequest */
    BulkOwnerRequest: {
      /** Interaction Ids */
      interaction_ids: string[];
      /**
       * Owner Id
       * Format: uuid
       */
      owner_id: string;
      /**
       * Reason
       * @default
       */
      reason: string;
    };
    /**
     * BulkResult
     * @description Частичный успех — обычный ответ: у каждой записи свой итог.
     */
    BulkResult: {
      /** Results */
      results: components["schemas"]["BulkItemResult"][];
      /** Succeeded */
      succeeded: number;
      /** Failed */
      failed: number;
    };
    /** BulkTransitionRequest */
    BulkTransitionRequest: {
      /** Interaction Ids */
      interaction_ids: string[];
      /**
       * To Stage Code
       * @description Код этапа назначения в версии процесса взаимодействия
       */
      to_stage_code: string;
      /**
       * Comment
       * @default
       */
      comment: string;
    };
    /** CatalogImportOut */
    CatalogImportOut: {
      /** Kind */
      kind: string;
      /**
       * Dry Run
       * @description Предпросмотр: в базе ничего не изменилось
       */
      dry_run: boolean;
      /** Created */
      created: number;
      /** Updated */
      updated: number;
      /** Unchanged */
      unchanged: number;
      /** Errors */
      errors: number;
      /** Rows */
      rows: components["schemas"]["CatalogRowOut"][];
    };
    /** CatalogItemCreate */
    CatalogItemCreate: {
      /** Name */
      name: string;
      /**
       * Code
       * @description Только для направлений
       */
      code?: string | null;
      /**
       * Short Name
       * @description Только для вузов
       */
      short_name?: string | null;
      /**
       * Region
       * @description Только для вузов
       */
      region?: string | null;
      /** City */
      city?: string | null;
      /**
       * Direction Id
       * @description Только для программ
       */
      direction_id?: string | null;
      /**
       * Vendor Id
       * @description Только для продуктов
       */
      vendor_id?: string | null;
    };
    /** CatalogItemOut */
    CatalogItemOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Archived At */
      archived_at: string | null;
    };
    /** CatalogRowOut */
    CatalogRowOut: {
      /**
       * Row No
       * @description Номер строки данных в файле, с 1
       */
      row_no: number;
      /**
       * Key
       * @description Чем строка опознана: название, код или пара вендор и продукт
       */
      key: string;
      /**
       * Action
       * @enum {string}
       */
      action: "created" | "updated" | "unchanged" | "error";
      /**
       * Detail
       * @description Что изменилось или почему строка не применена
       */
      detail: string | null;
    };
    /** ChannelOut */
    ChannelOut: {
      /**
       * Kind
       * @enum {string}
       */
      kind: "telegram" | "max" | "email";
      /** Name */
      name: string;
      /** Is Enabled */
      is_enabled: boolean;
      /**
       * Is Mock
       * @description Канал смотрит в заглушку, а не в настоящий сервис
       */
      is_mock: boolean;
      /**
       * Settings
       * @description Адрес API или почтового сервера, без секретов
       */
      settings: {
        [key: string]: unknown;
      };
      /**
       * Secret Ref
       * @description Имя переменной окружения с токеном или паролем
       */
      secret_ref: string | null;
      /**
       * Secret Configured
       * @description Переменная с секретом задана на сервере
       */
      secret_configured: boolean;
      /**
       * Kinds
       * @description Какие уведомления канал пересылает
       */
      kinds: (
        | "stalled_interaction"
        | "stage_changed"
        | "workflow_changed"
        | "channel_test"
      )[];
      /**
       * Updated At
       * Format: date-time
       */
      updated_at: string;
    };
    /**
     * ChannelUpdate
     * @description Пропущенное поле не меняется. Секрет задаётся именем переменной окружения `NOTIFY_*`.
     */
    ChannelUpdate: {
      /** Is Enabled */
      is_enabled?: boolean | null;
      /** Is Mock */
      is_mock?: boolean | null;
      /** Settings */
      settings?: {
        [key: string]: unknown;
      } | null;
      /** Secret Ref */
      secret_ref?: string | null;
      /** Kinds */
      kinds?:
        | (
            | "stalled_interaction"
            | "stage_changed"
            | "workflow_changed"
            | "channel_test"
          )[]
        | null;
    };
    /**
     * ChartOut
     * @description Данные и настройки ECharts: интерфейс и PDF рисуют график по одному описанию.
     */
    ChartOut: {
      /** Title */
      title: string;
      /** Labels */
      labels: string[];
      /** Values */
      values: number[];
      /**
       * Option
       * @description Готовые настройки ECharts
       */
      option: {
        [key: string]: unknown;
      };
    };
    /** ClientCreate */
    ClientCreate: {
      /**
       * Kind
       * @enum {string}
       */
      kind: "person" | "organization";
      /** Name */
      name: string;
      /**
       * Inn
       * @description ИНН организации: 10 или 12 цифр
       */
      inn?: string | null;
      /** City */
      city?: string | null;
      /** Email */
      email?: string | null;
      /** Phone */
      phone?: string | null;
    };
    /** ClientListItem */
    ClientListItem: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Kind
       * @enum {string}
       */
      kind: "person" | "organization";
      /**
       * Name
       * @description ФИО человека или наименование организации
       */
      name: string;
      /** Inn */
      inn: string | null;
      /** City */
      city: string | null;
    };
    /**
     * ClientOut
     * @description Карточка клиента. Email и телефон расшифровываются только по запросу карточки.
     */
    ClientOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Kind
       * @enum {string}
       */
      kind: "person" | "organization";
      /**
       * Name
       * @description ФИО человека или наименование организации
       */
      name: string;
      /** Inn */
      inn: string | null;
      /** City */
      city: string | null;
      /** Email */
      email: string | null;
      /** Phone */
      phone: string | null;
      /** Archived At */
      archived_at: string | null;
    };
    /** ClientRef */
    ClientRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Kind
       * @enum {string}
       */
      kind: "person" | "organization";
      /**
       * Name
       * @description ФИО человека или наименование организации
       */
      name: string;
    };
    /** ContactCreate */
    ContactCreate: {
      /** Full Name */
      full_name: string;
      /** Position */
      position?: string | null;
      /** Email */
      email?: string | null;
      /** Phone */
      phone?: string | null;
    };
    /**
     * ContactOut
     * @description Контакт вуза. Email и телефон расшифровываются только для того, кто их запросил.
     */
    ContactOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * University Id
       * Format: uuid
       */
      university_id: string;
      /** Full Name */
      full_name: string;
      /** Position */
      position: string | null;
      /** Email */
      email: string | null;
      /** Phone */
      phone: string | null;
      /** Archived At */
      archived_at: string | null;
    };
    /** ContractOut */
    ContractOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Number */
      number: string;
      /** Signed At */
      signed_at: string | null;
      /** License Signed At */
      license_signed_at: string | null;
      /** License Valid Until */
      license_valid_until: string | null;
      /** License Term Years */
      license_term_years: number | null;
      /** Transfer Status */
      transfer_status: string | null;
    };
    /** ContributionOut */
    ContributionOut: {
      /**
       * Metric
       * @description applications, students или streams
       */
      metric: string;
      /** Weight */
      weight: number;
      /**
       * Value
       * @description Значение метрики за период
       */
      value: number;
      /**
       * Normalized
       * @description Доля от лучшего в направлении, 0–100
       */
      normalized: number;
      /**
       * Contribution
       * @description Вклад метрики в балл
       */
      contribution: number;
    };
    /** CounterpartyGroupCreate */
    CounterpartyGroupCreate: {
      /** Code */
      code: string;
      /** Name */
      name: string;
      /** Description */
      description?: string | null;
      /**
       * Workflow Template Id
       * Format: uuid
       * @description Опубликованный процесс группы
       */
      workflow_template_id: string;
      /**
       * Position
       * @description Порядок в списках
       * @default 0
       */
      position: number;
    };
    /** CounterpartyGroupOut */
    CounterpartyGroupOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Code */
      code: string;
      /** Name */
      name: string;
      /** Description */
      description: string | null;
      /**
       * Workflow Template Id
       * Format: uuid
       * @description Процесс, по которому идут записи группы
       */
      workflow_template_id: string;
      /** Position */
      position: number;
    };
    /**
     * CounterpartyGroupUpdate
     * @description Пропущенное поле не меняется. Процесс группы с открытыми записями не заменяется.
     */
    CounterpartyGroupUpdate: {
      /** Name */
      name?: string | null;
      /** Description */
      description?: string | null;
      /** Workflow Template Id */
      workflow_template_id?: string | null;
      /** Position */
      position?: number | null;
    };
    /**
     * CounterpartyRef
     * @description Контрагент записи: вуз, человек или организация — одной ссылкой для списков.
     */
    CounterpartyRef: {
      /**
       * Kind
       * @enum {string}
       */
      kind: "university" | "person" | "organization";
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /**
       * Short Name
       * @description Сокращение вуза; у клиента совпадает с именем
       */
      short_name: string;
    };
    /** DeliveryOut */
    DeliveryOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Notification Id
       * Format: uuid
       */
      notification_id: string;
      /**
       * Channel Kind
       * @enum {string}
       */
      channel_kind: "telegram" | "max" | "email";
      /**
       * Status
       * @enum {string}
       */
      status: "pending" | "sent" | "failed";
      /** Attempts */
      attempts: number;
      /** Last Error */
      last_error: string | null;
      /**
       * Next Attempt At
       * Format: date-time
       */
      next_attempt_at: string;
      /** Sent At */
      sent_at: string | null;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
    };
    /** DialogOut */
    DialogOut: {
      peer: components["schemas"]["UserRef"];
      /**
       * Last Message
       * @description Начало последнего сообщения в переписке
       */
      last_message: string;
      /**
       * Last At
       * Format: date-time
       */
      last_at: string;
      /**
       * Unread
       * @description Сколько его сообщений вы ещё не читали
       */
      unread: number;
    };
    /** DialogsOut */
    DialogsOut: {
      /** Unread Total */
      unread_total: number;
      /** Items */
      items: components["schemas"]["DialogOut"][];
    };
    /** DirectionRef */
    DirectionRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Code */
      code: string;
      /** Name */
      name: string;
    };
    /** DocumentApplication */
    DocumentApplication: {
      /**
       * Id
       * Format: uuid
       * @description Ключ записи site_application
       */
      id: string;
      /**
       * External Id
       * @description Номер заявки на сайте
       */
      external_id: string;
      /**
       * Received At
       * Format: date-time
       */
      received_at: string;
    };
    /** DocumentContract */
    DocumentContract: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Number */
      number: string;
      /** Signed At */
      signed_at: string | null;
      /** License Valid Until */
      license_valid_until: string | null;
      /** Transfer Status */
      transfer_status: string | null;
    };
    /** DocumentCounterparty */
    DocumentCounterparty: {
      /**
       * Kind
       * @enum {string}
       */
      kind: "university" | "person" | "organization";
      /**
       * Id
       * Format: uuid
       * @description Ключ записи university или client
       */
      id: string;
      /** Name */
      name: string;
      /** Short Name */
      short_name: string;
      /** Region */
      region: string | null;
      /** City */
      city: string | null;
      /**
       * Inn
       * @description ИНН организации
       */
      inn: string | null;
    };
    /** DocumentFile */
    DocumentFile: {
      /**
       * Id
       * Format: uuid
       * @description Ключ записи attachment
       */
      id: string;
      /** Document Type */
      document_type: string | null;
      /** File Name */
      file_name: string;
      /** Mime Type */
      mime_type: string;
      /** Size Bytes */
      size_bytes: number;
      /**
       * Sha256
       * @description Контрольная сумма: сверка файла без его скачивания
       */
      sha256: string;
      /** Stage Code */
      stage_code: string;
      /**
       * Uploaded At
       * Format: date-time
       */
      uploaded_at: string;
      /**
       * Storage
       * @description Где лежит файл: backend (s3 или local), bucket и key
       */
      storage: {
        [key: string]: string;
      };
    };
    /** DocumentGroup */
    DocumentGroup: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Code */
      code: string;
      /** Name */
      name: string;
    };
    /** DocumentPerson */
    DocumentPerson: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Full Name */
      full_name: string;
    };
    /** DocumentProduct */
    DocumentProduct: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Vendor Name */
      vendor_name: string;
    };
    /** DocumentProgram */
    DocumentProgram: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Direction Code */
      direction_code: string;
      /** Direction Name */
      direction_name: string;
      /**
       * Lms Course Ref
       * @description Курс программы в LMS, если известен
       */
      lms_course_ref: string | null;
    };
    /**
     * DocumentRecord
     * @description Ключ записи в базе CRM.
     */
    DocumentRecord: {
      /**
       * Table
       * @default interaction
       * @constant
       */
      table: "interaction";
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Version
       * @description Растёт с каждым изменением: получатель отбрасывает устаревшие документы
       */
      version: number;
    };
    /** DocumentStatus */
    DocumentStatus: {
      /**
       * State
       * @enum {string}
       */
      state: "active" | "paused" | "completed" | "cancelled";
      /** Stage Code */
      stage_code: string;
      /** Stage Name */
      stage_name: string;
      /**
       * Stage Entered At
       * Format: date-time
       */
      stage_entered_at: string;
      /**
       * Workflow Template Id
       * Format: uuid
       */
      workflow_template_id: string;
      /**
       * Workflow Version Id
       * Format: uuid
       */
      workflow_version_id: string;
    };
    /**
     * ErrorCode
     * @enum {string}
     */
    ErrorCode:
      | "VALIDATION_ERROR"
      | "AUTH_REQUIRED"
      | "AUTH_FORBIDDEN"
      | "NOT_FOUND"
      | "INTERACTION_VERSION_CONFLICT"
      | "INTERACTION_DUPLICATE"
      | "WF_TRANSITION_NOT_ALLOWED"
      | "WF_COMMENT_REQUIRED"
      | "WF_ATTACHMENT_REQUIRED"
      | "WF_VERSION_NOT_DRAFT"
      | "WF_MIGRATION_MAP_INCOMPLETE"
      | "FILE_TYPE_NOT_ALLOWED"
      | "FILE_TOO_LARGE"
      | "IMPORT_MAPPING_INVALID"
      | "REPORT_TOO_LARGE"
      | "INTEGRATION_UNAVAILABLE"
      | "INTERNAL_ERROR";
    /** EscalationRunOut */
    EscalationRunOut: {
      /**
       * Notified
       * @description Сколько уведомлений о зависших записях создано
       */
      notified: number;
    };
    /** FieldError */
    FieldError: {
      /** Field */
      field: string;
      /** Message */
      message: string;
    };
    /** GroupRef */
    GroupRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Code */
      code: string;
      /** Name */
      name: string;
    };
    /** HTTPValidationError */
    HTTPValidationError: {
      /** Detail */
      detail?: components["schemas"]["ValidationError"][];
    };
    /** HealthOut */
    HealthOut: {
      /**
       * Status
       * @constant
       */
      status: "ok";
      /** Version */
      version: string;
      /**
       * Database
       * @constant
       */
      database: "ok";
      /**
       * Storage
       * @constant
       */
      storage: "ok";
    };
    /** HelpTopicOut */
    HelpTopicOut: {
      /** Slug */
      slug: string;
      /** Title */
      title: string;
      /** Summary */
      summary: string;
      /**
       * Body
       * @description Текст раздела в Markdown
       */
      body: string;
    };
    /** HelpTopicRef */
    HelpTopicRef: {
      /** Slug */
      slug: string;
      /** Title */
      title: string;
      /** Summary */
      summary: string;
    };
    /** ImportBatchOut */
    ImportBatchOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** File Name */
      file_name: string;
      /**
       * File Kind
       * @description xlsx, xls или csv
       */
      file_kind: string;
      /**
       * Encoding
       * @description Кодировка, в которой прочитан файл: указанная вручную или определённая
       */
      encoding: string | null;
      /**
       * Delimiter
       * @description Разделитель колонок CSV
       */
      delimiter: string | null;
      /** Status */
      status: string;
      /**
       * Headers
       * @description Колонки файла в исходном порядке
       */
      headers: string[];
      /**
       * Column Map
       * @description Поле модели → заголовок колонки
       */
      column_map: {
        [key: string]: string;
      };
      /**
       * Suggested Map
       * @description Подсказка по заголовкам ТЗ
       */
      suggested_map: {
        [key: string]: string;
      };
      /**
       * Fields
       * @description Поля модели, доступные для сопоставления
       */
      fields: string[];
      /** Required Fields */
      required_fields: string[];
      /** Total Rows */
      total_rows: number;
      /**
       * Stats
       * @description Сколько строк в каждом решении
       */
      stats: {
        [key: string]: number;
      };
      /**
       * Rows
       * @description Первые строки для предпросмотра
       */
      rows: components["schemas"]["RowPreview"][];
    };
    /** ImportProfileOut */
    ImportProfileOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** File Kind */
      file_kind: string;
      /** Column Map */
      column_map: {
        [key: string]: string;
      };
    };
    /** IntegrationSourceOut */
    IntegrationSourceOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Kind
       * @description lms или site
       */
      kind: string;
      /** Name */
      name: string;
      /** Base Url */
      base_url: string;
      /** Is Mock */
      is_mock: boolean;
      /** Schedule Cron */
      schedule_cron: string | null;
      /** Last Sync At */
      last_sync_at: string | null;
      /**
       * Push Enabled
       * @description Система принимает изменения записей CRM
       */
      push_enabled: boolean;
      /** Last Push At */
      last_push_at: string | null;
    };
    /**
     * InteractionCreate
     * @description Новая запись вручную. Контрагент — ровно один: вуз или клиент.
     */
    InteractionCreate: {
      /**
       * Group Id
       * Format: uuid
       */
      group_id: string;
      /** University Id */
      university_id?: string | null;
      /** Client Id */
      client_id?: string | null;
      /**
       * Program Id
       * Format: uuid
       */
      program_id: string;
      /**
       * Product Id
       * @description Продукт из программы; у продуктонезависимой программы пусто
       */
      product_id?: string | null;
      /**
       * Owner Id
       * @description Ответственный; по умолчанию — тот, кто создаёт запись
       */
      owner_id?: string | null;
      /**
       * Comment
       * @description Попадёт в первую запись истории
       * @default
       */
      comment: string;
    };
    /** InteractionDetail */
    InteractionDetail: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** @description Группа контрагентов: от неё зависит процесс */
      group: components["schemas"]["GroupRef"];
      /** @description Вуз или клиент — одной ссылкой */
      counterparty: components["schemas"]["CounterpartyRef"];
      /** @description Вуз, если контрагент — вуз */
      university: components["schemas"]["UniversityRef"] | null;
      /** @description Клиент, если контрагент — не вуз */
      client: components["schemas"]["ClientRef"] | null;
      program: components["schemas"]["ProgramRef"];
      /** @description Пусто у продуктонезависимой программы */
      product: components["schemas"]["ProductRef"] | null;
      owner: components["schemas"]["UserRef"];
      stage: components["schemas"]["StageRef"];
      /**
       * Stage Entered At
       * Format: date-time
       */
      stage_entered_at: string;
      /** Days On Stage */
      days_on_stage: number;
      /** Norm Days */
      norm_days: number | null;
      /** Status */
      status: string;
      /**
       * Version
       * @description Передаётся в expected_version при переходе
       */
      version: number;
      /**
       * Last Activity At
       * Format: date-time
       */
      last_activity_at: string;
      /** Open Signals */
      open_signals: components["schemas"]["SignalBrief"][];
      /**
       * Workflow Version Id
       * Format: uuid
       */
      workflow_version_id: string;
      contract: components["schemas"]["ContractOut"] | null;
      /** History */
      history: components["schemas"]["TransitionOut"][];
      /** Allowed Transitions */
      allowed_transitions: components["schemas"]["AllowedTransitionOut"][];
      /** Signals */
      signals: components["schemas"]["SignalOut"][];
    };
    /** InteractionDocument */
    InteractionDocument: {
      /**
       * Format
       * @default radar-vuzov/interaction@1
       * @constant
       */
      format: "radar-vuzov/interaction@1";
      record: components["schemas"]["DocumentRecord"];
      group: components["schemas"]["DocumentGroup"];
      status: components["schemas"]["DocumentStatus"];
      /** @description Ответственный КАМ */
      owner: components["schemas"]["DocumentPerson"];
      counterparty: components["schemas"]["DocumentCounterparty"];
      program: components["schemas"]["DocumentProgram"];
      product: components["schemas"]["DocumentProduct"] | null;
      contract: components["schemas"]["DocumentContract"] | null;
      /** Files */
      files: components["schemas"]["DocumentFile"][];
      /** Site Applications */
      site_applications: components["schemas"]["DocumentApplication"][];
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Updated At
       * Format: date-time
       */
      updated_at: string;
      /**
       * Exported At
       * Format: date-time
       */
      exported_at: string;
    };
    /** InteractionListItem */
    InteractionListItem: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** @description Группа контрагентов: от неё зависит процесс */
      group: components["schemas"]["GroupRef"];
      /** @description Вуз или клиент — одной ссылкой */
      counterparty: components["schemas"]["CounterpartyRef"];
      /** @description Вуз, если контрагент — вуз */
      university: components["schemas"]["UniversityRef"] | null;
      /** @description Клиент, если контрагент — не вуз */
      client: components["schemas"]["ClientRef"] | null;
      program: components["schemas"]["ProgramRef"];
      /** @description Пусто у продуктонезависимой программы */
      product: components["schemas"]["ProductRef"] | null;
      owner: components["schemas"]["UserRef"];
      stage: components["schemas"]["StageRef"];
      /**
       * Stage Entered At
       * Format: date-time
       */
      stage_entered_at: string;
      /** Days On Stage */
      days_on_stage: number;
      /** Norm Days */
      norm_days: number | null;
      /** Status */
      status: string;
      /**
       * Version
       * @description Передаётся в expected_version при переходе
       */
      version: number;
      /**
       * Last Activity At
       * Format: date-time
       */
      last_activity_at: string;
      /** Open Signals */
      open_signals: components["schemas"]["SignalBrief"][];
    };
    /** InteractionRef */
    InteractionRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      group: components["schemas"]["GroupRef"];
      counterparty: components["schemas"]["CounterpartyRef"];
      university: components["schemas"]["UniversityRef"] | null;
      client: components["schemas"]["ClientRef"] | null;
      program: components["schemas"]["ProgramRef"];
      product: components["schemas"]["ProductRef"] | null;
      owner: components["schemas"]["UserRef"];
    };
    /** MappingUpdate */
    MappingUpdate: {
      /**
       * Column Map
       * @description Поле модели → заголовок колонки файла
       */
      column_map: {
        [key: string]: string;
      };
      /**
       * Save As Profile
       * @description Сохранить соответствие под этим именем
       */
      save_as_profile?: string | null;
    };
    /** MeOut */
    MeOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Full Name */
      full_name: string;
      /** Email */
      email: string;
      role: components["schemas"]["Role"];
      team: components["schemas"]["TeamRef"] | null;
      /**
       * Scope
       * @enum {string}
       */
      scope: "own" | "team" | "all";
    };
    /** MessageCreate */
    MessageCreate: {
      /**
       * Recipient Id
       * Format: uuid
       */
      recipient_id: string;
      /** Body */
      body: string;
      /**
       * Interaction Id
       * @description Запись, о которой сообщение
       */
      interaction_id?: string | null;
    };
    /**
     * MessageInteractionRef
     * @description Запись, о которой речь. Показывается только тому, кому она доступна.
     */
    MessageInteractionRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Label */
      label: string;
    };
    /** MessageOut */
    MessageOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      sender: components["schemas"]["UserRef"];
      recipient: components["schemas"]["UserRef"];
      /** Body */
      body: string;
      /** @description Запись, о которой сообщение, если она доступна читателю */
      interaction?: components["schemas"]["MessageInteractionRef"] | null;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Read At */
      read_at: string | null;
    };
    /** NormUpdate */
    NormUpdate: {
      /**
       * Norm Days
       * @description Новая норма этапа в днях
       */
      norm_days: number;
    };
    /** NoteCreate */
    NoteCreate: {
      /** Text */
      text: string;
    };
    /** NoteOut */
    NoteOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Text */
      text: string;
      author: components["schemas"]["UserRef"];
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
    };
    /** NotificationOut */
    NotificationOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Kind
       * @enum {string}
       */
      kind:
        | "stalled_interaction"
        | "stage_changed"
        | "workflow_changed"
        | "channel_test";
      /** Title */
      title: string;
      /** Body */
      body: string;
      /** Interaction Id */
      interaction_id: string | null;
      /** Payload */
      payload: {
        [key: string]: unknown;
      };
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Read At */
      read_at: string | null;
    };
    /** OutboxEntryOut */
    OutboxEntryOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Interaction Id
       * Format: uuid
       */
      interaction_id: string;
      /**
       * Reason
       * @description Что изменилось: created, transition, owner, attachment и др.
       */
      reason: string;
      /**
       * Status
       * @description pending, sent или failed
       */
      status: string;
      /** Attempts */
      attempts: number;
      /**
       * Next Attempt At
       * Format: date-time
       */
      next_attempt_at: string;
      /** Last Error */
      last_error: string | null;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Sent At */
      sent_at: string | null;
    };
    /** OwnerChange */
    OwnerChange: {
      /**
       * Owner Id
       * Format: uuid
       */
      owner_id: string;
      /**
       * Reason
       * @default
       */
      reason: string;
      /**
       * Expected Version
       * @description Версия записи, которую видел пользователь
       */
      expected_version: number;
    };
    /** Page[ClientListItem] */
    Page_ClientListItem_: {
      /** Items */
      items: components["schemas"]["ClientListItem"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[InteractionDocument] */
    Page_InteractionDocument_: {
      /** Items */
      items: components["schemas"]["InteractionDocument"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[InteractionListItem] */
    Page_InteractionListItem_: {
      /** Items */
      items: components["schemas"]["InteractionListItem"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[NotificationOut] */
    Page_NotificationOut_: {
      /** Items */
      items: components["schemas"]["NotificationOut"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[SignalListItem] */
    Page_SignalListItem_: {
      /** Items */
      items: components["schemas"]["SignalListItem"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /** Page[UniversityOut] */
    Page_UniversityOut_: {
      /** Items */
      items: components["schemas"]["UniversityOut"][];
      /** Total */
      total: number;
      /** Page */
      page: number;
      /** Page Size */
      page_size: number;
    };
    /**
     * ParticipantContactOut
     * @description Полный контакт: показывается по запросу и пишется в аудит.
     */
    ParticipantContactOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Full Name */
      full_name: string;
      /** Email */
      email: string | null;
    };
    /** ParticipantCountsOut */
    ParticipantCountsOut: {
      /** Students */
      students: number;
      /** Teachers */
      teachers: number;
    };
    /** ParticipantCreate */
    ParticipantCreate: {
      /**
       * Role
       * @default student
       * @enum {string}
       */
      role: "student" | "teacher";
      /** Full Name */
      full_name: string;
      /** Email */
      email?: string | null;
      /**
       * External Ref
       * @description Идентификатор в LMS
       */
      external_ref?: string | null;
    };
    /** ParticipantImportOut */
    ParticipantImportOut: {
      /** Dry Run */
      dry_run: boolean;
      /** Created */
      created: number;
      /** Updated */
      updated: number;
      /** Unchanged */
      unchanged: number;
      /** Errors */
      errors: number;
      /** Rows */
      rows: components["schemas"]["ParticipantRowOut"][];
    };
    /** ParticipantOut */
    ParticipantOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Role
       * @enum {string}
       */
      role: "student" | "teacher";
      /** Full Name */
      full_name: string;
      /**
       * Email
       * @description Почта скрыта: и***@вуз.рф. Целиком — в карточке участника
       */
      email: string | null;
      /** Has Email */
      has_email: boolean;
      /**
       * Source
       * @description manual — завели руками, import — из файла, lms — из LMS
       */
      source: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
    };
    /** ParticipantRowOut */
    ParticipantRowOut: {
      /** Row No */
      row_no: number;
      /**
       * Key
       * @description ФИО строки — по нему видно, о ком речь
       */
      key: string;
      /**
       * Action
       * @enum {string}
       */
      action: "created" | "updated" | "unchanged" | "error";
      /** Detail */
      detail: string | null;
    };
    /** ParticipantsOut */
    ParticipantsOut: {
      counts: components["schemas"]["ParticipantCountsOut"];
      /** Items */
      items: components["schemas"]["ParticipantOut"][];
    };
    /** PriorityUpdate */
    PriorityUpdate: {
      /**
       * Priority
       * @description Чем больше, тем выше в списке; 0 — не задан
       */
      priority: number;
    };
    /**
     * Problem
     * @description Тело ответа с ошибкой.
     */
    Problem: {
      /**
       * Type
       * @default about:blank
       */
      type: string;
      /** Title */
      title: string;
      /** Status */
      status: number;
      code: components["schemas"]["ErrorCode"];
      /** Detail */
      detail?: string | null;
      /** Trace Id */
      trace_id: string;
      /**
       * Errors
       * @default []
       */
      errors: components["schemas"]["FieldError"][];
    };
    /** ProductRef */
    ProductRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      vendor: components["schemas"]["VendorRef"];
    };
    /** ProgramRef */
    ProgramRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      direction: components["schemas"]["DirectionRef"];
      /**
       * Priority
       * @description Ручной приоритет курса, 0 — не задан
       */
      priority: number;
    };
    /**
     * PublishPreview
     * @description Что изменит публикация: данные для окна подтверждения.
     */
    PublishPreview: {
      /** Renamed */
      renamed: components["schemas"]["StageRenameOut"][];
      /**
       * Moves
       * @description Удалённые этапы и этапы, записи с которых карта переносит на другой
       */
      moves: components["schemas"]["StageMoveOut"][];
      /** Added */
      added: components["schemas"]["StageRef"][];
      /**
       * Moved Interactions
       * @description Сколько открытых записей перейдёт на новую схему
       */
      moved_interactions: number;
      /**
       * Requires Admin
       * @description Черновик переименовывает этапы: опубликовать его может только администратор
       */
      requires_admin: boolean;
    };
    /** PublishRequest */
    PublishRequest: {
      /**
       * Migration Map
       * @description Код этапа прежней схемы → код новой. Необязательна: записи с удалённого этапа сами переходят на ближайший предыдущий этап, а если его нет — на следующий
       */
      migration_map?: {
        [key: string]: string;
      };
    };
    /** RatingOut */
    RatingOut: {
      /**
       * Entity
       * @enum {string}
       */
      entity: "program" | "university";
      /** Weights */
      weights: {
        [key: string]: number;
      };
      /**
       * Order
       * @description Чем отсортированы строки: баллом или ручным приоритетом
       * @default score
       * @enum {string}
       */
      order: "score" | "priority";
      /** Rows */
      rows: components["schemas"]["RatingRowOut"][];
    };
    /** RatingRowOut */
    RatingRowOut: {
      /** Place */
      place: number;
      /**
       * Place Change
       * @description Насколько поднялась позиция к предыдущему периоду; null — раньше её не было
       */
      place_change: number | null;
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Direction Name */
      direction_name: string;
      /** Score */
      score: number;
      /**
       * Priority
       * @description Ручной приоритет курса, 0 — не задан
       */
      priority: number;
      /** Contributions */
      contributions: components["schemas"]["ContributionOut"][];
      /**
       * Complete
       * @description Есть ли все три метрики за период
       */
      complete: boolean;
      /** Missing Metrics */
      missing_metrics: string[];
    };
    /** ReadAllOut */
    ReadAllOut: {
      /**
       * Updated
       * @description Сколько уведомлений отмечено прочитанными
       */
      updated: number;
    };
    /** ReadOut */
    ReadOut: {
      /** Updated */
      updated: number;
    };
    /**
     * ReportCreate
     * @description Те же фильтры, что у списка взаимодействий, плюс колонки и формат файла.
     */
    ReportCreate: {
      /**
       * Format
       * @default xlsx
       * @enum {string}
       */
      format: "xlsx" | "xls" | "csv" | "pdf" | "json";
      /**
       * Encoding
       * @description Кодировка CSV: utf-8 (с BOM, без потерь) или windows-1251 для старых программ
       * @default utf-8
       * @enum {string}
       */
      encoding: "utf-8" | "windows-1251";
      /** Period From */
      period_from?: string | null;
      /** Period To */
      period_to?: string | null;
      /** Group Id */
      group_id?: string[];
      /** University Id */
      university_id?: string[];
      /** Direction Id */
      direction_id?: string[];
      /** Program Id */
      program_id?: string[];
      /** Product Id */
      product_id?: string[];
      /** Owner Id */
      owner_id?: string[];
      /** Stage Code */
      stage_code?: string[];
      /**
       * Status
       * @description Состояние записи; без фильтра отменённые не попадают
       */
      status?: ("active" | "paused" | "completed" | "cancelled")[];
      /** Search */
      search?: string | null;
      /**
       * Columns
       * @description Из набора: group, counterparty, university, direction, program, product, stage, owner, contract, license_valid_until, days_on_stage, signals
       */
      columns?: string[];
    };
    /** ReportJobOut */
    ReportJobOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Status
       * @description queued, running, done или failed
       */
      status: string;
      /**
       * Progress
       * @description Процент готовности
       */
      progress: number;
      /** Format */
      format: string;
      /** Row Count */
      row_count: number | null;
      /**
       * Error Code
       * @description Код ошибки из каталога, если отчёт не построен
       */
      error_code: string | null;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Finished At */
      finished_at: string | null;
    };
    /**
     * Role
     * @enum {string}
     */
    Role: "kam" | "manager" | "admin";
    /** RowPreview */
    RowPreview: {
      /** Row No */
      row_no: number;
      /**
       * Resolution
       * @description new, update, conflict, skip или needs_program
       */
      resolution: string;
      /**
       * Detail
       * @description Причина, если строка требует внимания
       */
      detail: string | null;
      /** University */
      university: string;
      /** Product */
      product: string;
      /** Contract Number */
      contract_number: string;
    };
    /** SavedViewCreate */
    SavedViewCreate: {
      /**
       * Page
       * @enum {string}
       */
      page: "interactions" | "radar" | "reports" | "rating" | "clients";
      /** Name */
      name: string;
      /**
       * Filters
       * @description Параметры запроса страницы: сервер их не толкует
       */
      filters?: {
        [key: string]: unknown;
      };
      /**
       * Columns
       * @description Колонки списка в нужном порядке
       */
      columns?: string[];
    };
    /** SavedViewOut */
    SavedViewOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Page
       * @enum {string}
       */
      page: "interactions" | "radar" | "reports" | "rating" | "clients";
      /** Name */
      name: string;
      /** Filters */
      filters: {
        [key: string]: unknown;
      };
      /** Columns */
      columns: string[];
      /**
       * Updated At
       * Format: date-time
       */
      updated_at: string;
    };
    /** SavedViewUpdate */
    SavedViewUpdate: {
      /** Name */
      name?: string | null;
      /** Filters */
      filters?: {
        [key: string]: unknown;
      } | null;
      /** Columns */
      columns?: string[] | null;
    };
    /** SettingOut */
    SettingOut: {
      /** Key */
      key: string;
      /** Description */
      description: string;
      /**
       * Value
       * @description Действующее значение, в том числе по умолчанию
       */
      value: {
        [key: string]: unknown;
      };
      /**
       * Is Default
       * @description Настройку не сохраняли: действует значение по умолчанию
       */
      is_default: boolean;
      /** Updated At */
      updated_at: string | null;
    };
    /** SettingUpdate */
    SettingUpdate: {
      /** Value */
      value: {
        [key: string]: unknown;
      };
    };
    /**
     * Severity
     * @enum {string}
     */
    Severity: "low" | "medium" | "high";
    /** SignalBrief */
    SignalBrief: {
      kind: components["schemas"]["SignalKind"];
      severity: components["schemas"]["Severity"];
    };
    /**
     * SignalKind
     * @enum {string}
     */
    SignalKind:
      "stage_overdue" | "license_expiring" | "missing_document" | "inactivity";
    /** SignalListItem */
    SignalListItem: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      kind: components["schemas"]["SignalKind"];
      severity: components["schemas"]["Severity"];
      /**
       * Detected At
       * Format: date-time
       */
      detected_at: string;
      /** Resolved At */
      resolved_at: string | null;
      /**
       * Message
       * @description Готовая строка для интерфейса, проверяемая по evidence
       */
      message: string;
      /**
       * Evidence
       * @description Доказательство сигнала: этап, дни на этапе, норма и её источник (norm_source: manual или suggested), дата окончания лицензии или последней активности
       */
      evidence: {
        [key: string]: unknown;
      };
      interaction: components["schemas"]["InteractionRef"];
    };
    /** SignalOut */
    SignalOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      kind: components["schemas"]["SignalKind"];
      severity: components["schemas"]["Severity"];
      /**
       * Detected At
       * Format: date-time
       */
      detected_at: string;
      /** Resolved At */
      resolved_at: string | null;
      /**
       * Message
       * @description Готовая строка для интерфейса, проверяемая по evidence
       */
      message: string;
      /**
       * Evidence
       * @description Доказательство сигнала: этап, дни на этапе, норма и её источник (norm_source: manual или suggested), дата окончания лицензии или последней активности
       */
      evidence: {
        [key: string]: unknown;
      };
    };
    /**
     * SignalSummaryOut
     * @description Матрица «КАМ × вид сигнала» для тепловой карты руководителя.
     */
    SignalSummaryOut: {
      /** Kinds */
      kinds: components["schemas"]["SignalKind"][];
      /** Rows */
      rows: components["schemas"]["SummaryRow"][];
      /** Total */
      total: number;
    };
    /** SiteApplicationOut */
    SiteApplicationOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** External Id */
      external_id: string;
      /** University Name */
      university_name: string;
      /** Program Name */
      program_name: string;
      /** Contact Name */
      contact_name: string | null;
      /** Comment */
      comment: string | null;
      /**
       * Received At
       * Format: date-time
       */
      received_at: string;
      /**
       * Match Status
       * @description matched или unmatched
       */
      match_status: string;
      /** Interaction Id */
      interaction_id: string | null;
    };
    /** SourceUpdate */
    SourceUpdate: {
      /**
       * Push Enabled
       * @description Отправлять ли системе изменения записей
       */
      push_enabled: boolean;
    };
    /**
     * StageDraft
     * @description Этап черновика: код неизменяем и связывает норму с этапом между версиями.
     */
    StageDraft: {
      /** Code */
      code: string;
      /** Name */
      name: string;
      /** Position */
      position: number;
      /**
       * Kind
       * @default normal
       * @enum {string}
       */
      kind: "start" | "normal" | "final";
      /**
       * Bulk Allowed
       * @default false
       */
      bulk_allowed: boolean;
      /** Required Document Types */
      required_document_types?: string[];
      /** Norm Days */
      norm_days?: number | null;
    };
    /**
     * StageMoveOut
     * @description Куда переедут открытые записи этапа прежней схемы.
     */
    StageMoveOut: {
      /** From Code */
      from_code: string;
      /** From Name */
      from_name: string;
      /**
       * Stage Removed
       * @description Этапа нет в новой схеме
       */
      stage_removed: boolean;
      /** Open Interactions */
      open_interactions: number;
      /** To Code */
      to_code: string;
      /** To Name */
      to_name: string;
      /**
       * Automatic
       * @description Этап выбран автоматически, а не картой переноса
       */
      automatic: boolean;
    };
    /** StageNormOut */
    StageNormOut: {
      /** Stage Code */
      stage_code: string;
      /** Stage Name */
      stage_name: string;
      /** Norm Days */
      norm_days: number;
      /**
       * Source
       * @description manual — задана вручную, suggested — принята подсказка
       */
      source: string;
      /**
       * Suggested Median Days
       * @description Типичный срок этапа по завершённым переходам
       */
      suggested_median_days: number | null;
      /**
       * Suggested Percentile Days
       * @description 80-й перцентиль: срок, в который укладывается большинство
       */
      suggested_percentile_days: number | null;
      /**
       * Sample Size
       * @description Сколько завершённых этапов легло в подсказку
       */
      sample_size: number | null;
    };
    /** StageOut */
    StageOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Code */
      code: string;
      /** Name */
      name: string;
      /** Position */
      position: number;
      /** Kind */
      kind: string;
      /** Bulk Allowed */
      bulk_allowed: boolean;
      /** Required Document Types */
      required_document_types: string[];
      /** Norm Days */
      norm_days: number | null;
    };
    /** StageRef */
    StageRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Code */
      code: string;
      /** Name */
      name: string;
      /** Position */
      position: number;
    };
    /** StageRename */
    StageRename: {
      /** Name */
      name: string;
    };
    /** StageRenameOut */
    StageRenameOut: {
      /** Code */
      code: string;
      /** Old Name */
      old_name: string;
      /** New Name */
      new_name: string;
    };
    /**
     * StatusChange
     * @description Приостановка, завершение, отмена и возврат в работу. Этап сам по себе ничего не завершает.
     */
    StatusChange: {
      /**
       * Status
       * @enum {string}
       */
      status: "active" | "paused" | "completed" | "cancelled";
      /**
       * Reason
       * @description Обязателен для паузы и отмены: почему
       * @default
       */
      reason: string;
      /**
       * Expected Version
       * @description Версия записи, которую видел пользователь
       */
      expected_version: number;
    };
    /** SummaryRow */
    SummaryRow: {
      owner: components["schemas"]["UserRef"];
      /**
       * Counts
       * @description Открытые сигналы по видам
       */
      counts: {
        [key: string]: number;
      };
      /** Total */
      total: number;
    };
    /** SyncRunOut */
    SyncRunOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Source Id
       * Format: uuid
       */
      source_id: string;
      /**
       * Direction
       * @description pull — забрали данные, push — отправили изменения
       */
      direction: string;
      /**
       * Started At
       * Format: date-time
       */
      started_at: string;
      /** Finished At */
      finished_at: string | null;
      /**
       * Status
       * @description running, done или failed
       */
      status: string;
      /** Stats */
      stats: {
        [key: string]: unknown;
      };
      /** Error Code */
      error_code: string | null;
    };
    /** TeamCreate */
    TeamCreate: {
      /** Name */
      name: string;
      /** Manager User Id */
      manager_user_id?: string | null;
    };
    /** TeamOut */
    TeamOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Manager User Id */
      manager_user_id: string | null;
    };
    /** TeamRef */
    TeamRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
    };
    /** TransitionCreate */
    TransitionCreate: {
      /**
       * To Stage Id
       * Format: uuid
       */
      to_stage_id: string;
      /**
       * Comment
       * @default
       */
      comment: string;
      /**
       * Expected Version
       * @description Версия записи, которую видел пользователь
       */
      expected_version: number;
      /** Attachment Ids */
      attachment_ids?: string[];
    };
    /** TransitionDraft */
    TransitionDraft: {
      /** From Code */
      from_code: string;
      /** To Code */
      to_code: string;
      /**
       * Requires Comment
       * @default true
       */
      requires_comment: boolean;
      /**
       * Requires Attachment
       * @default false
       */
      requires_attachment: boolean;
    };
    /** TransitionOut */
    TransitionOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      from_stage: components["schemas"]["StageRef"] | null;
      to_stage: components["schemas"]["StageRef"];
      /**
       * Occurred At
       * Format: date-time
       */
      occurred_at: string;
      actor: components["schemas"]["UserRef"] | null;
      /** Comment */
      comment: string | null;
      /** Source */
      source: string;
    };
    /** TransitionResult */
    TransitionResult: {
      transition: components["schemas"]["TransitionOut"];
      interaction: components["schemas"]["InteractionDetail"];
    };
    /** TransitionRuleOut */
    TransitionRuleOut: {
      /**
       * From Stage Id
       * Format: uuid
       */
      from_stage_id: string;
      /**
       * To Stage Id
       * Format: uuid
       */
      to_stage_id: string;
      /** Requires Comment */
      requires_comment: boolean;
      /** Requires Attachment */
      requires_attachment: boolean;
    };
    /** UniversityOut */
    UniversityOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Short Name */
      short_name: string;
      /** Region */
      region: string;
      /** City */
      city: string | null;
      /** Interactions Count */
      interactions_count: number;
      /** Open Signals Count */
      open_signals_count: number;
    };
    /** UniversityRef */
    UniversityRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Short Name */
      short_name: string;
      /** Region */
      region: string;
    };
    /** UserOut */
    UserOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Full Name */
      full_name: string;
      /** Email */
      email: string;
      role: components["schemas"]["Role"];
    };
    /** UserRef */
    UserRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Full Name */
      full_name: string;
    };
    /** ValidationError */
    ValidationError: {
      /** Location */
      loc: (string | number)[];
      /** Message */
      msg: string;
      /** Error Type */
      type: string;
      /** Input */
      input?: unknown;
      /** Context */
      ctx?: Record<string, never>;
    };
    /** VendorRef */
    VendorRef: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
    };
    /** VersionOut */
    VersionOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Template Id
       * Format: uuid
       */
      template_id: string;
      /** Version No */
      version_no: number;
      /**
       * Status
       * @description draft, published или retired
       */
      status: string;
      /** Published At */
      published_at: string | null;
      /** Stages */
      stages: components["schemas"]["StageOut"][];
      /** Transitions */
      transitions: components["schemas"]["TransitionRuleOut"][];
    };
    /**
     * VersionPatch
     * @description Что меняем в черновике. Пропущенное поле остаётся как было.
     */
    VersionPatch: {
      /** Stages */
      stages?: components["schemas"]["StageDraft"][] | null;
      /** Transitions */
      transitions?: components["schemas"]["TransitionDraft"][] | null;
    };
    /** WeightsOut */
    WeightsOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** W Applications */
      w_applications: number;
      /** W Students */
      w_students: number;
      /** W Streams */
      w_streams: number;
      /** Is Default */
      is_default: boolean;
    };
    /** WeightsUpdate */
    WeightsUpdate: {
      /** W Applications */
      w_applications: number;
      /** W Students */
      w_students: number;
      /** W Streams */
      w_streams: number;
    };
    /** WorkflowOut */
    WorkflowOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /**
       * Template Id
       * Format: uuid
       */
      template_id: string;
      /** Name */
      name: string;
      /** Version No */
      version_no: number;
      /** Stages */
      stages: components["schemas"]["StageOut"][];
      /** Transitions */
      transitions: components["schemas"]["TransitionRuleOut"][];
    };
    /**
     * WorkflowSummaryOut
     * @description Шаблон процесса: действующая схема, черновик изменений и группы, которые по нему работают.
     */
    WorkflowSummaryOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Is Default */
      is_default: boolean;
      /** Published Version Id */
      published_version_id: string | null;
      /** Version No */
      version_no: number | null;
      /**
       * Draft Version Id
       * @description Черновик изменений, если начат
       */
      draft_version_id: string | null;
      /** Groups */
      groups: components["schemas"]["GroupRef"][];
    };
    /** WorkflowTemplateCreate */
    WorkflowTemplateCreate: {
      /** Name */
      name: string;
    };
    /** WorkflowTemplateOut */
    WorkflowTemplateOut: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      /** Name */
      name: string;
      /** Is Default */
      is_default: boolean;
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
  health_api_health_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HealthOut"];
        };
      };
      /** @description INTERNAL_ERROR */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_me_api_v1_me_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["MeOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_universities_api_v1_universities_get: {
    parameters: {
      query?: {
        /** @description Название или регион */
        search?: string | null;
        /** @description Номер страницы, с 1 */
        page?: number;
        /** @description Размер страницы */
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_UniversityOut_"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_university_api_v1_universities__university_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        university_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["UniversityOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_groups_api_v1_counterparty_groups_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CounterpartyGroupOut"][];
        };
      };
      /** @description С прошлого запроса ничего не изменилось */
      304: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_directions_api_v1_directions_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["DirectionRef"][];
        };
      };
      /** @description С прошлого запроса ничего не изменилось */
      304: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_programs_api_v1_programs_get: {
    parameters: {
      query?: {
        /** @description ИТ-направление */
        direction_id?: string[] | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProgramRef"][];
        };
      };
      /** @description С прошлого запроса ничего не изменилось */
      304: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  put_program_priority_api_v1_programs__program_id__priority_put: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        program_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["PriorityUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProgramRef"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_products_api_v1_products_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ProductRef"][];
        };
      };
      /** @description С прошлого запроса ничего не изменилось */
      304: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_users_api_v1_users_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["UserOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_clients_api_v1_clients_get: {
    parameters: {
      query?: {
        /** @description Имя, название или ИНН */
        search?: string | null;
        /** @description Человек или организация */
        kind?: ("person" | "organization") | null;
        /** @description Номер страницы, с 1 */
        page?: number;
        /** @description Размер страницы */
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_ClientListItem_"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_client_api_v1_clients_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ClientCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ClientOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_client_api_v1_clients__client_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        client_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ClientOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_default_workflow_api_v1_workflows_default_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["WorkflowOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_norms_api_v1_workflows_default_norms_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["StageNormOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  put_norm_api_v1_workflows_default_norms__stage_code__put: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        stage_code: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["NormUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["StageNormOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_accept_suggestion_api_v1_workflows_default_norms__stage_code__accept_suggestion_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        stage_code: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["StageNormOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_workflows_api_v1_workflows_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["WorkflowSummaryOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_template_api_v1_workflows_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["WorkflowTemplateCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["WorkflowTemplateOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_workflow_api_v1_workflows__template_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        template_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["WorkflowOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_template_norms_api_v1_workflows__template_id__norms_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        template_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["StageNormOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  put_template_norm_api_v1_workflows__template_id__norms__stage_code__put: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        template_id: string;
        stage_code: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["NormUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["StageNormOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_template_accept_suggestion_api_v1_workflows__template_id__norms__stage_code__accept_suggestion_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        template_id: string;
        stage_code: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["StageNormOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_version_api_v1_workflows__template_id__versions_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        template_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["VersionOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  patch_workflow_version_api_v1_workflow_versions__version_id__patch: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        version_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["VersionPatch"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["VersionOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description WF_VERSION_NOT_DRAFT */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  patch_stage_api_v1_stages__stage_id__patch: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        stage_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["StageRename"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["StageRef"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_publish_preview_api_v1_workflow_versions__version_id__publish_preview_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        version_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["PublishRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["PublishPreview"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description WF_VERSION_NOT_DRAFT */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR · WF_MIGRATION_MAP_INCOMPLETE */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_publish_api_v1_workflow_versions__version_id__publish_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        version_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["PublishRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["VersionOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description WF_VERSION_NOT_DRAFT */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR · WF_MIGRATION_MAP_INCOMPLETE */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_interactions_api_v1_interactions_get: {
    parameters: {
      query?: {
        /** @description Номер страницы, с 1 */
        page?: number;
        /** @description Размер страницы */
        page_size?: number;
        /** @description Группа контрагентов */
        group_id?: string[] | null;
        /** @description Клиент вне вузов */
        client_id?: string[] | null;
        /** @description Вуз */
        university_id?: string[] | null;
        /** @description ИТ-направление */
        direction_id?: string[] | null;
        /** @description ИТ-программа */
        program_id?: string[] | null;
        /** @description ИТ-продукт */
        product_id?: string[] | null;
        /** @description КАМ */
        owner_id?: string[] | null;
        /** @description Код текущего этапа */
        stage_code?: string[] | null;
        /** @description Состояние записи; без фильтра отменённые скрыты */
        status?: ("active" | "paused" | "completed" | "cancelled")[] | null;
        /** @description Есть открытый сигнал */
        has_signal?: boolean | null;
        /** @description Начало периода, UTC */
        period_from?: string | null;
        /** @description Конец периода, UTC */
        period_to?: string | null;
        /** @description Контрагент, программа или продукт */
        search?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_InteractionListItem_"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_interaction_api_v1_interactions_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["InteractionCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["InteractionDetail"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description INTERACTION_DUPLICATE */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_interaction_api_v1_interactions__interaction_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["InteractionDetail"];
        };
      };
      /** @description С прошлого запроса ничего не изменилось */
      304: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_transition_api_v1_interactions__interaction_id__transitions_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["TransitionCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TransitionResult"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description INTERACTION_VERSION_CONFLICT · WF_TRANSITION_NOT_ALLOWED */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR · WF_COMMENT_REQUIRED · WF_ATTACHMENT_REQUIRED */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_notes_api_v1_interactions__interaction_id__notes_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NoteOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_note_api_v1_interactions__interaction_id__notes_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["NoteCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NoteOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  put_status_api_v1_interactions__interaction_id__status_put: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["StatusChange"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["InteractionDetail"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description INTERACTION_VERSION_CONFLICT · INTERACTION_DUPLICATE · WF_TRANSITION_NOT_ALLOWED */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_bulk_transitions_api_v1_interactions_bulk_transitions_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["BulkTransitionRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["BulkResult"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  put_owner_api_v1_interactions__interaction_id__owner_put: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["OwnerChange"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["InteractionDetail"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description INTERACTION_VERSION_CONFLICT */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_bulk_owner_api_v1_interactions_bulk_owner_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["BulkOwnerRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["BulkResult"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_interaction_document_api_v1_interactions__interaction_id__export_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["InteractionDocument"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_exchange_api_v1_exchange_interactions_get: {
    parameters: {
      query?: {
        /** @description Изменённые не раньше этого момента, ISO 8601 */
        updated_since?: string | null;
        /** @description Группа контрагентов */
        group_id?: string[] | null;
        /** @description Номер страницы, с 1 */
        page?: number;
        /** @description Размер страницы */
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_InteractionDocument_"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_attachments_api_v1_interactions__interaction_id__attachments_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AttachmentOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_attachment_api_v1_interactions__interaction_id__attachments_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": components["schemas"]["Body_post_attachment_api_v1_interactions__interaction_id__attachments_post"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AttachmentOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description FILE_TOO_LARGE */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description FILE_TYPE_NOT_ALLOWED */
      415: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_attachment_file_api_v1_attachments__attachment_id__file_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        attachment_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Файл вложения с исходным именем */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/octet-stream": unknown;
        };
      };
      /** @description С прошлого запроса ничего не изменилось */
      304: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_import_api_v1_imports_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": components["schemas"]["Body_post_import_api_v1_imports_post"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ImportBatchOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description FILE_TOO_LARGE */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description FILE_TYPE_NOT_ALLOWED */
      415: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  put_mapping_api_v1_imports__batch_id__mapping_put: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["MappingUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ImportBatchOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR · IMPORT_MAPPING_INVALID */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_apply_api_v1_imports__batch_id__apply_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        batch_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ApplyResult"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_import_profiles_api_v1_import_profiles_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ImportProfileOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_integrations_api_v1_integrations_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["IntegrationSourceOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_sync_api_v1_integrations__source_id__sync_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        source_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SyncRunOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  patch_source_api_v1_integrations__source_id__patch: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        source_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["SourceUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["IntegrationSourceOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_push_api_v1_integrations__source_id__push_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        source_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SyncRunOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_outbox_api_v1_integrations__source_id__outbox_get: {
    parameters: {
      query?: {
        /** @description Состояние отправки */
        status?: string | null;
      };
      header?: never;
      path: {
        source_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["OutboxEntryOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_runs_api_v1_integrations__source_id__runs_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        source_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SyncRunOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_applications_api_v1_site_applications_get: {
    parameters: {
      query?: {
        /** @description Состояние сопоставления */
        match_status?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SiteApplicationOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_match_api_v1_site_applications__application_id__match_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        application_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ApplicationMatch"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SiteApplicationOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_signals_api_v1_signals_get: {
    parameters: {
      query?: {
        /** @description Номер страницы, с 1 */
        page?: number;
        /** @description Размер страницы */
        page_size?: number;
        /** @description Группа контрагентов */
        group_id?: string[] | null;
        /** @description Вид сигнала */
        kind?: components["schemas"]["SignalKind"][] | null;
        /** @description Серьёзность */
        severity?: components["schemas"]["Severity"][] | null;
        /** @description КАМ */
        owner_id?: string[] | null;
        /** @description Вуз */
        university_id?: string[] | null;
        /** @description Начало периода, UTC */
        period_from?: string | null;
        /** @description Конец периода, UTC */
        period_to?: string | null;
        /** @description Контрагент, программа или продукт */
        search?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_SignalListItem_"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_signals_summary_api_v1_signals_summary_get: {
    parameters: {
      query?: {
        /** @description Группа контрагентов */
        group_id?: string[] | null;
        /** @description Вид сигнала */
        kind?: components["schemas"]["SignalKind"][] | null;
        /** @description Серьёзность */
        severity?: components["schemas"]["Severity"][] | null;
        /** @description КАМ */
        owner_id?: string[] | null;
        /** @description Вуз */
        university_id?: string[] | null;
        /** @description Начало периода, UTC */
        period_from?: string | null;
        /** @description Конец периода, UTC */
        period_to?: string | null;
        /** @description Контрагент, программа или продукт */
        search?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SignalSummaryOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_reports_api_v1_reports_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ReportJobOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_report_api_v1_reports_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ReportCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      202: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ReportJobOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR · REPORT_TOO_LARGE */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_report_api_v1_reports__report_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        report_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ReportJobOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_report_file_api_v1_reports__report_id__file_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        report_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Файл отчёта */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/octet-stream": unknown;
        };
      };
      /** @description С прошлого запроса ничего не изменилось */
      304: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_rating_api_v1_analytics_rating_get: {
    parameters: {
      query?: {
        /** @description Что сравниваем */
        entity?: "program" | "university";
        /** @description Начало периода */
        period_from?: string | null;
        /** @description Конец периода */
        period_to?: string | null;
        /** @description ИТ-направление */
        direction_id?: string[] | null;
        /** @description Порядок строк: по баллу или по ручному приоритету */
        order?: "score" | "priority";
        w_applications?: number | null;
        w_students?: number | null;
        w_streams?: number | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["RatingOut"];
        };
      };
      /** @description С прошлого запроса ничего не изменилось */
      304: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_weights_api_v1_analytics_rating_weights_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["WeightsOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  put_weights_api_v1_analytics_rating_weights_put: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["WeightsUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["WeightsOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_funnel_api_v1_analytics_stats_funnel_get: {
    parameters: {
      query?: {
        /** @description Группа контрагентов; по умолчанию — вузы */
        group_id?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ChartOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_stage_durations_api_v1_analytics_stats_stage_durations_get: {
    parameters: {
      query?: {
        /** @description Группа контрагентов; по умолчанию — вузы */
        group_id?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ChartOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_stats_report_api_v1_analytics_stats_report_get: {
    parameters: {
      query?: {
        /** @description Группа контрагентов; по умолчанию — вузы */
        group_id?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Файл со статистикой */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/pdf": unknown;
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_distribution_api_v1_analytics_stats_distribution_get: {
    parameters: {
      query?: {
        /** @description Группа контрагентов */
        group_id?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ChartOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_users_api_v1_admin_users_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AdminUserOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  patch_user_api_v1_admin_users__user_id__patch: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        user_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["AdminUserUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AdminUserOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_teams_api_v1_admin_teams_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TeamOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_team_api_v1_admin_teams_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["TeamCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TeamOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_rules_api_v1_admin_access_rules_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AccessRuleOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_rule_api_v1_admin_access_rules_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["AccessRuleCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AccessRuleOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  delete_rule_api_v1_admin_access_rules__rule_id__delete: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        rule_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_settings_api_v1_admin_settings_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SettingOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  put_setting_api_v1_admin_settings__key__put: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        key: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["SettingUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SettingOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_audit_api_v1_admin_audit_get: {
    parameters: {
      query?: {
        action?: string | null;
        entity_kind?: string | null;
        limit?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AuditEntryOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_catalog_item_api_v1_admin_catalogs__kind__post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        kind: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CatalogItemCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CatalogItemOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_catalog_import_api_v1_admin_catalogs__kind__import_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        kind: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": components["schemas"]["Body_post_catalog_import_api_v1_admin_catalogs__kind__import_post"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CatalogImportOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description FILE_TOO_LARGE */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR · IMPORT_MAPPING_INVALID */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_catalog_export_api_v1_admin_catalogs__kind__export_get: {
    parameters: {
      query?: {
        /** @description Формат файла */
        format?: "json" | "csv" | "xlsx";
        /** @description Кодировка CSV */
        encoding?: "utf-8" | "windows-1251";
        /** @description Вместе с архивными записями */
        include_archived?: boolean;
      };
      header?: never;
      path: {
        kind: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Файл справочника */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": unknown;
          "text/csv": unknown;
          "application/octet-stream": unknown;
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_catalog_archive_api_v1_admin_catalogs__kind___item_id__archive_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        kind: string;
        item_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CatalogItemOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_group_api_v1_admin_counterparty_groups_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CounterpartyGroupCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CounterpartyGroupOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  patch_group_api_v1_admin_counterparty_groups__group_id__patch: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        group_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["CounterpartyGroupUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CounterpartyGroupOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_group_archive_api_v1_admin_counterparty_groups__group_id__archive_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        group_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["CounterpartyGroupOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_contacts_api_v1_universities__university_id__contacts_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        university_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ContactOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_contact_api_v1_universities__university_id__contacts_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        university_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ContactCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ContactOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_contact_archive_api_v1_contacts__contact_id__archive_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        contact_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ContactOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_notifications_api_v1_notifications_get: {
    parameters: {
      query?: {
        /** @description Только непрочитанные */
        unread?: boolean;
        /** @description Номер страницы, с 1 */
        page?: number;
        /** @description Размер страницы */
        page_size?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Page_NotificationOut_"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_read_all_api_v1_notifications_read_all_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ReadAllOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_read_api_v1_notifications__notification_id__read_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        notification_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["NotificationOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_addresses_api_v1_me_notification_addresses_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AddressOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  put_address_api_v1_me_notification_addresses__channel_kind__put: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        channel_kind: "telegram" | "max" | "email";
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["AddressUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["AddressOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_channels_api_v1_admin_notification_channels_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ChannelOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  patch_channel_api_v1_admin_notification_channels__channel_kind__patch: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        channel_kind: "telegram" | "max" | "email";
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ChannelUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ChannelOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_channel_test_api_v1_admin_notification_channels__channel_kind__test_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        channel_kind: "telegram" | "max" | "email";
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["DeliveryOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_deliveries_api_v1_admin_notification_deliveries_get: {
    parameters: {
      query?: {
        /** @description Состояние доставки */
        status?: ("pending" | "sent" | "failed") | null;
        limit?: number;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["DeliveryOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_escalations_run_api_v1_admin_escalations_run_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["EscalationRunOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_FORBIDDEN */
      403: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_topics_api_v1_help_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HelpTopicRef"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_image_api_v1_help_images__name__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        name: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Изображение */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "image/png": unknown;
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_topic_api_v1_help__slug__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        slug: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HelpTopicOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_dialogs_api_v1_messages_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["DialogsOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_message_api_v1_messages_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["MessageCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["MessageOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_messages_api_v1_messages__peer_id__get: {
    parameters: {
      query?: {
        /** @description Сколько последних сообщений */
        limit?: number;
      };
      header?: never;
      path: {
        peer_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["MessageOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_read_api_v1_messages__peer_id__read_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        peer_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ReadOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_participants_api_v1_interactions__interaction_id__participants_get: {
    parameters: {
      query?: {
        /** @description Только одна роль */
        role?: ("student" | "teacher") | null;
      };
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ParticipantsOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_participant_api_v1_interactions__interaction_id__participants_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["ParticipantCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ParticipantOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_participant_contact_api_v1_participants__participant_id__contact_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        participant_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ParticipantContactOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  delete_participant_api_v1_participants__participant_id__delete: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        participant_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_participants_import_api_v1_interactions__interaction_id__participants_import_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "multipart/form-data": components["schemas"]["Body_post_participants_import_api_v1_interactions__interaction_id__participants_import_post"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ParticipantImportOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description FILE_TOO_LARGE */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR · IMPORT_MAPPING_INVALID */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_participants_export_api_v1_interactions__interaction_id__participants_export_get: {
    parameters: {
      query?: {
        /** @description Формат файла */
        format?: "json" | "csv" | "xlsx";
        /** @description Кодировка CSV */
        encoding?: "utf-8" | "windows-1251";
      };
      header?: never;
      path: {
        interaction_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Файл списка */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": unknown;
          "text/csv": unknown;
          "application/octet-stream": unknown;
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_views_api_v1_saved_views_get: {
    parameters: {
      query?: {
        /** @description Только для одной страницы */
        page?:
          ("interactions" | "radar" | "reports" | "rating" | "clients") | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SavedViewOut"][];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  post_view_api_v1_saved_views_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["SavedViewCreate"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SavedViewOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  remove_view_api_v1_saved_views__view_id__delete: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        view_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  patch_view_api_v1_saved_views__view_id__patch: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        view_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["SavedViewUpdate"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["SavedViewOut"];
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
  read_events_api_v1_events_get: {
    parameters: {
      query?: never;
      header?: {
        "Last-Event-ID"?: string | null;
      };
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description События области видимости пользователя */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "text/event-stream": unknown;
        };
      };
      /** @description AUTH_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/problem+json": components["schemas"]["Problem"];
        };
      };
    };
  };
}
