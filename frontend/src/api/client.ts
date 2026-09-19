import type {
  Schema,
  Me,
  Interaction,
  Workflow,
  Transition,
  InteractionFilters,
  SignalFilters,
  UniversityFilters,
  University,
} from "./types";
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public traceId?: string,
    public fields: Schema["FieldError"][] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }
}
export function queryString(values: object) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    if (value === undefined || value === null || value === "") continue;
    for (const item of Array.isArray(value) ? value : [value])
      query.append(key, String(item));
  }
  return query.size ? `?${query}` : "";
}
export class ApiClient {
  constructor(
    private base: string,
    private headers: () => Promise<Record<string, string>>,
  ) {}
  private async request<T>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    const headers = new Headers(await this.headers());
    headers.set("Accept", "application/json");
    if (options.body) headers.set("Content-Type", "application/json");
    let response: Response;
    try {
      response = await fetch(`${this.base.replace(/\/$/, "")}${path}`, {
        ...options,
        headers,
        redirect: "error",
      });
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError")
        throw error;
      throw new ApiError(
        0,
        "",
        "Нет связи с API. Проверьте подключение и повторите запрос.",
      );
    }
    const payload = await response.json().catch(() => null);
    if (!response.ok)
      throw new ApiError(
        response.status,
        payload?.code || "",
        payload?.detail ||
          payload?.title ||
          "Сервис временно недоступен. Повторите запрос.",
        payload?.trace_id,
        payload?.errors || [],
      );
    if (payload === null)
      throw new ApiError(response.status, "", "API вернул некорректный ответ.");
    return payload as T;
  }
  me = (signal?: AbortSignal) => this.request<Me>("/api/v1/me", { signal });
  workflow = (signal?: AbortSignal) =>
    this.request<Workflow>("/api/v1/workflows/default", { signal });
  groups = (signal?: AbortSignal) =>
    this.request<Schema["CounterpartyGroupOut"][]>(
      "/api/v1/counterparty-groups",
      { signal },
    );
  workflowByTemplate = (id: string, signal?: AbortSignal) =>
    this.request<Workflow>(`/api/v1/workflows/${encodeURIComponent(id)}`, {
      signal,
    });
  interactions = (filters: InteractionFilters = {}, signal?: AbortSignal) =>
    this.request<Schema["Page_InteractionListItem_"]>(
      "/api/v1/interactions" + queryString(filters),
      { signal },
    );
  interaction = (id: string, signal?: AbortSignal) =>
    this.request<Interaction>(
      `/api/v1/interactions/${encodeURIComponent(id)}`,
      { signal },
    );
  signals = (filters: SignalFilters = {}, signal?: AbortSignal) =>
    this.request<Schema["Page_SignalListItem_"]>(
      "/api/v1/signals" + queryString(filters),
      { signal },
    );
  universities = (filters: UniversityFilters = {}, signal?: AbortSignal) =>
    this.request<Schema["Page_UniversityOut_"]>(
      "/api/v1/universities" + queryString(filters),
      { signal },
    );
  university = (id: string, signal?: AbortSignal) =>
    this.request<University>(`/api/v1/universities/${encodeURIComponent(id)}`, {
      signal,
    });
  users = (signal?: AbortSignal) =>
    this.request<Schema["UserOut"][]>("/api/v1/users", { signal });
  transition = (id: string, payload: Transition) =>
    this.request<Schema["TransitionResult"]>(
      `/api/v1/interactions/${encodeURIComponent(id)}/transitions`,
      { method: "POST", body: JSON.stringify(payload) },
    );
}
