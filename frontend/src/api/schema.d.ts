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
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /** AllowedTransitionOut */
    AllowedTransitionOut: {
      to_stage: components["schemas"]["StageRef"];
      /** Requires Comment */
      requires_comment: boolean;
      /** Requires Attachment */
      requires_attachment: boolean;
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
    /**
     * Role
     * @enum {string}
     */
    Role: "kam" | "manager" | "admin";
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
      /** Message */
      message: string;
      /** Evidence */
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
      /** Message */
      message: string;
      /** Evidence */
      evidence: {
        [key: string]: unknown;
      };
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
          "application/json": components["schemas"]["Problem"];
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
          "application/json": components["schemas"]["Problem"];
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
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
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
      /** @description AUTH_REQUIRED, NOT_FOUND */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_REQUIRED, NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
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
          "application/json": components["schemas"]["Problem"];
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
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
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
          "application/json": components["schemas"]["Problem"];
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
          "application/json": components["schemas"]["Problem"];
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
      /** @description AUTH_REQUIRED, NOT_FOUND */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_REQUIRED, NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
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
      /** @description AUTH_REQUIRED, VALIDATION_ERROR */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_REQUIRED, VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
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
      /** @description AUTH_REQUIRED, NOT_FOUND */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_REQUIRED, NOT_FOUND */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
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
      /** @description AUTH_REQUIRED, NOT_FOUND, INTERACTION_VERSION_CONFLICT, WF_COMMENT_REQUIRED */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_REQUIRED, NOT_FOUND, INTERACTION_VERSION_CONFLICT, WF_COMMENT_REQUIRED */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_REQUIRED, NOT_FOUND, INTERACTION_VERSION_CONFLICT, WF_COMMENT_REQUIRED */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_REQUIRED, NOT_FOUND, INTERACTION_VERSION_CONFLICT, WF_COMMENT_REQUIRED */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
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
      /** @description AUTH_REQUIRED, VALIDATION_ERROR */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
      /** @description AUTH_REQUIRED, VALIDATION_ERROR */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Problem"];
        };
      };
    };
  };
}
