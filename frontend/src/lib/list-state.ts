import type { Schema } from "../api/types";
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export const filterKeys = [
  "q",
  "group",
  "kind",
  "severity",
  "stage",
  "owner",
  "direction",
  "page",
] as const;
export type FilterKey = (typeof filterKeys)[number];
export function readListState(params: URLSearchParams) {
  const kind = params.get("kind") || "";
  const severity = params.get("severity") || "";
  const page = Number(params.get("page") || 1);
  const stage = params.get("stage") || "";
  return {
    search: (params.get("q") || "").slice(0, 100),
    group: uuid.test(params.get("group") || "") ? params.get("group")! : "",
    direction: uuid.test(params.get("direction") || "")
      ? params.get("direction")!
      : "",
    owner: uuid.test(params.get("owner") || "") ? params.get("owner")! : "",
    stage: /^[a-z0-9_-]{1,100}$/i.test(stage) ? stage : "",
    kind: ([
      "stage_overdue",
      "license_expiring",
      "missing_document",
      "inactivity",
    ].includes(kind)
      ? kind
      : "") as Schema["SignalKind"] | "",
    severity: (["high", "medium", "low"].includes(severity) ? severity : "") as
      Schema["Severity"] | "",
    page: Number.isSafeInteger(page) && page > 0 && page <= 100000 ? page : 1,
  };
}
export function updateListState(
  current: URLSearchParams,
  patch: Partial<Record<FilterKey, string | number | null>>,
) {
  const next = new URLSearchParams(current);
  if (Object.keys(patch).some((key) => key !== "page")) next.delete("page");
  if ("group" in patch) next.delete("stage");
  for (const [key, value] of Object.entries(patch)) {
    if (value === null || value === "" || (key === "page" && value === 1))
      next.delete(key);
    else next.set(key, String(value));
  }
  return next;
}
export function listReturnTo(value: unknown, fallback = "/interactions") {
  if (typeof value !== "string") return fallback;
  const path = value.split("?")[0];
  return /^\/(radar|interactions|universities(?:\/[0-9a-f-]{36})?)$/.test(path)
    ? value
    : fallback;
}
export const recordStatus: Record<string, string> = {
  active: "В работе",
  paused: "На паузе",
  completed: "Завершено",
  cancelled: "Отменено",
};
export function pageRange(page: number, total: number, size = 20) {
  if (!total || (page - 1) * size >= total) return `0 из ${total}`;
  return `${(page - 1) * size + 1}–${Math.min(page * size, total)} из ${total}`;
}
