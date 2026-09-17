// Generated from contracts/openapi.yaml. Do not edit.
export interface paths {
  "/api/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Состояние сервиса и базы данных */
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
    get?: never;
    put?: never;
    /** Создать шаблон процесса */
    post: operations["post_template_api_v1_workflows_post"];
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
     * @description Единственное изменение, разрешённое в опубликованной версии.
     */
    patch: operations["patch_stage_api_v1_stages__stage_id__patch"];
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
     * Опубликовать версию
     * @description Открытые взаимодействия переезжают на новую версию переходом `migration`, а прежняя версия становится `retired`. Карта переноса нужна для занятых этапов.
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
    post?: never;
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
     * @description История, допустимые переходы с требованиями и открытые сигналы.
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
     * Загрузить выгрузку xls или xlsx
     * @description Возвращает колонки файла и подсказку соответствия по заголовкам ТЗ.
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
  "/api/v1/integrations/{source_id}/runs": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Журнал запусков источника */
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
     * @description Отчёт строится в фоне: ответ содержит id задания, дальше состояние смотрят в `GET /api/v1/reports/{id}`. Колонки: university, direction, program, product, stage, owner, contract, license_valid_until, days_on_stage, signals.
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
    /** Воронка по этапам */
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
    /** Средняя длительность этапов */
    get: operations["read_stage_durations_api_v1_analytics_stats_stage_durations_get"];
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
    /** Распределение по направлениям */
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
     * @description Пороги радара, веса по умолчанию и прочее; изменение пишется в аудит.
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
      scope_kind: "university" | "direction" | "program";
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
    /** Body_post_import_api_v1_imports_post */
    Body_post_import_api_v1_imports_post: {
      /**
       * File
       * @description Книга Excel с выгрузкой
       */
      file: string;
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
    /** FieldError */
    FieldError: {
      /** Field */
      field: string;
      /** Message */
      message: string;
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
      /** File Kind */
      file_kind: string;
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
    };
    /** InteractionDetail */
    InteractionDetail: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      university: components["schemas"]["UniversityRef"];
      program: components["schemas"]["ProgramRef"];
      product: components["schemas"]["ProductRef"];
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
    /** InteractionListItem */
    InteractionListItem: {
      /**
       * Id
       * Format: uuid
       */
      id: string;
      university: components["schemas"]["UniversityRef"];
      program: components["schemas"]["ProgramRef"];
      product: components["schemas"]["ProductRef"];
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
      university: components["schemas"]["UniversityRef"];
      program: components["schemas"]["ProgramRef"];
      product: components["schemas"]["ProductRef"];
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
    };
    /** PublishRequest */
    PublishRequest: {
      /**
       * Migration Map
       * @description Код этапа старой версии → код новой; нужен для занятых этапов
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
      format: "xlsx" | "xls" | "pdf" | "json";
      /** Period From */
      period_from?: string | null;
      /** Period To */
      period_to?: string | null;
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
      /** Search */
      search?: string | null;
      /**
       * Columns
       * @description Из набора: university, direction, program, product, stage, owner, contract, license_valid_until, days_on_stage, signals
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
    /** SettingOut */
    SettingOut: {
      /** Key */
      key: string;
      /** Value */
      value: {
        [key: string]: unknown;
      };
      /**
       * Updated At
       * Format: date-time
       */
      updated_at: string;
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
        /** @description Есть открытый сигнал */
        has_signal?: boolean | null;
        /** @description Начало периода, UTC */
        period_from?: string | null;
        /** @description Конец периода, UTC */
        period_to?: string | null;
        /** @description Вуз, программа или продукт */
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
        /** @description Вуз, программа или продукт */
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
        /** @description Вуз, программа или продукт */
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
    };
  };
  read_stage_durations_api_v1_analytics_stats_stage_durations_get: {
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
    };
  };
  read_distribution_api_v1_analytics_stats_distribution_get: {
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
