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
  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(await this.headers());
    headers.set("Accept", "application/json");
    if (options.body && !(options.body instanceof FormData))
      headers.set("Content-Type", "application/json");
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
    if (response.status === 204) return undefined as T;
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
  get = <T>(path: string, filters: object = {}, signal?: AbortSignal) =>
    this.request<T>("/api/v1" + path + queryString(filters), { signal });
  send = <T>(path: string, body: unknown = {}, method = "POST") =>
    this.request<T>("/api/v1" + path, { method, body: JSON.stringify(body) });
  upload = <T>(path: string, body: FormData) =>
    this.request<T>(path, { method: "POST", body });
  async file(path: string, expected?: "pdf") {
    let response: Response;
    const headers = await this.headers();
    try {
      response = await fetch(this.base.replace(/\/$/, "") + path, {
        headers,
        redirect: "error",
      });
    } catch {
      throw new ApiError(0, "", "Нет связи с API. Не удалось скачать файл.");
    }
    if (!response.ok) {
      const problem = await response.json().catch(() => null);
      throw new ApiError(
        response.status,
        problem?.code || "",
        problem?.detail || "Не удалось скачать файл.",
        problem?.trace_id,
      );
    }
    const blob = await response.blob();
    if (
      expected === "pdf" &&
      (!blob.type.toLowerCase().startsWith("application/pdf") ||
        (await blob.slice(0, 5).text()) !== "%PDF-" ||
        !(await blob.slice(-1024).text()).includes("%%EOF"))
    )
      throw new ApiError(
        200,
        "",
        "Сервис вернул некорректный PDF. Повторите загрузку отчёта.",
      );
    return blob;
  }
  async events(
    signal: AbortSignal,
    onEvent: (event: string, id: string) => void,
    lastId = "",
  ) {
    const headers = await this.headers();
    if (lastId) headers["Last-Event-ID"] = lastId;
    const response = await fetch(
      this.base.replace(/\/$/, "") + "/api/v1/events",
      { headers, signal, redirect: "error" },
    );
    if (!response.ok || !response.body)
      throw new Error("Поток обновлений недоступен");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    try {
      while (!signal.aborted) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer = (buffer + decoder.decode(value, { stream: true })).replace(
          /\r\n/g,
          "\n",
        );
        let boundary: number;
        while ((boundary = buffer.indexOf("\n\n")) >= 0) {
          const block = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          const event = block.match(/^event: ?(.+)$/m)?.[1];
          lastId = block.match(/^id: ?(.+)$/m)?.[1] || lastId;
          if (event) onEvent(event, lastId);
        }
      }
    } finally {
      reader.releaseLock();
    }
    return lastId;
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
