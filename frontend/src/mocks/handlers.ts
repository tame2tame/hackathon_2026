import {
  serviceHandlers,
  unsupportedServiceAction,
  setServiceRecordsSource,
} from "./service-handlers";
import { http, HttpResponse } from "msw";
import {
  allowedFor,
  createFixtures,
  mockUsers,
  mockWorkflow,
  mockGroups,
  mockClientWorkflow,
} from "./fixtures";
import type { Interaction, Schema, Signal, University } from "../api/types";
let records = createFixtures();
setServiceRecordsSource(() => records);
export const resetFixtures = () => {
  records = createFixtures();
};
const problem = (code: Schema["ErrorCode"], status: number, title: string) =>
  HttpResponse.json(
    {
      type: "about:blank",
      title,
      status,
      code,
      detail: title,
      trace_id: "mock-trace",
      errors: [],
    },
    { status, headers: { "Content-Type": "application/problem+json" } },
  );
function user(request: Request) {
  return mockUsers.find((u) => u.email === request.headers.get("X-Dev-User"));
}
function scope(request: Request) {
  const u = user(request);
  return u
    ? records.filter((i) => u.role !== "kam" || i.owner.id === u.id)
    : null;
}
function paged<T>(items: T[], url: URL) {
  const page = Number(url.searchParams.get("page") || 1);
  const size = Number(url.searchParams.get("page_size") || 50);
  if (
    !Number.isInteger(page) ||
    page < 1 ||
    !Number.isInteger(size) ||
    size < 1 ||
    size > 200
  )
    return problem("VALIDATION_ERROR", 422, "Неверная страница");
  return HttpResponse.json({
    items: items.slice((page - 1) * size, page * size),
    total: items.length,
    page,
    page_size: size,
  });
}
function matching(i: Interaction, url: URL) {
  const q = url.searchParams;
  const search = q.get("search")?.toLowerCase() || "";
  const text =
    `${i.counterparty.name} ${i.counterparty.short_name} ${i.program.name} ${i.product?.name || ""}`.toLowerCase();
  return (
    text.includes(search) &&
    [
      ["group_id", i.group.id],
      ["university_id", i.university?.id || ""],
      ["program_id", i.program.id],
      ["product_id", i.product?.id || ""],
      ["owner_id", i.owner.id],
      ["direction_id", i.program.direction.id],
      ["stage_code", i.stage.code],
    ].every(([key, value]) => !q.has(key) || q.getAll(key).includes(value)) &&
    (!q.has("has_signal") ||
      Boolean(i.signals.length) === (q.get("has_signal") === "true"))
  );
}
function universityRows(items: Interaction[]): University[] {
  return [
    ...new Map(
      items
        .filter(
          (
            i,
          ): i is Interaction & {
            university: NonNullable<Interaction["university"]>;
          } => i.university !== null,
        )
        .map((i) => [
          i.university.id,
          {
            ...i.university,
            city: i.university.region,
            interactions_count: items.filter(
              (x) => x.university?.id === i.university.id,
            ).length,
            open_signals_count: items
              .filter((x) => x.university?.id === i.university.id)
              .reduce((n, x) => n + x.signals.length, 0),
          },
        ]),
    ).values(),
  ];
}
export const handlers = [
  ...serviceHandlers,
  http.get("*/api/v1/counterparty-groups", ({ request }) =>
    user(request)
      ? HttpResponse.json(mockGroups)
      : problem("AUTH_REQUIRED", 401, "Нужна авторизация"),
  ),
  http.get("*/api/v1/workflows/:id", ({ request, params }) => {
    if (!user(request))
      return problem("AUTH_REQUIRED", 401, "Нужна авторизация");
    const workflow = [mockWorkflow, mockClientWorkflow].find(
      (w) =>
        w.template_id === params.id ||
        (params.id === "default" && w === mockWorkflow),
    );
    return workflow
      ? HttpResponse.json(workflow)
      : problem("NOT_FOUND", 404, "Процесс недоступен");
  }),
  http.get("*/api/v1/me", ({ request }) =>
    user(request)
      ? HttpResponse.json(user(request))
      : problem("AUTH_REQUIRED", 401, "Нужна авторизация"),
  ),
  http.get("*/api/v1/workflows/default", ({ request }) =>
    user(request)
      ? HttpResponse.json(mockWorkflow)
      : problem("AUTH_REQUIRED", 401, "Нужна авторизация"),
  ),
  http.get("*/api/v1/users", ({ request }) => {
    const u = user(request);
    return u
      ? HttpResponse.json(
          mockUsers.filter((x) => u.role !== "kam" || x.id === u.id),
        )
      : problem("AUTH_REQUIRED", 401, "Нужна авторизация");
  }),
  http.get("*/api/v1/interactions", ({ request }) => {
    const items = scope(request);
    const url = new URL(request.url);
    return items
      ? paged(
          items
            .filter((i) => matching(i, url))
            .map(
              ({
                history,
                signals,
                allowed_transitions,
                contract,
                workflow_version_id,
                ...i
              }) => {
                void history;
                void signals;
                void allowed_transitions;
                void contract;
                void workflow_version_id;
                return i;
              },
            ),
          url,
        )
      : problem("AUTH_REQUIRED", 401, "Нужна авторизация");
  }),
  http.get("*/api/v1/interactions/:id", ({ request, params }) => {
    const items = scope(request);
    if (!items) return problem("AUTH_REQUIRED", 401, "Нужна авторизация");
    const item = items.find((i) => i.id === params.id);
    return item
      ? HttpResponse.json(item)
      : problem("NOT_FOUND", 404, "Запись недоступна");
  }),
  http.get("*/api/v1/signals", ({ request }) => {
    const items = scope(request);
    if (!items) return problem("AUTH_REQUIRED", 401, "Нужна авторизация");
    const url = new URL(request.url);
    const q = url.searchParams;
    const signals: Signal[] = items
      .filter((i) => matching(i, url))
      .flatMap((i) =>
        i.signals.map((s) => ({
          ...s,
          interaction: {
            id: i.id,
            group: i.group,
            counterparty: i.counterparty,
            client: i.client,
            university: i.university,
            program: i.program,
            product: i.product,
            owner: i.owner,
          },
        })),
      )
      .filter(
        (s) =>
          (!q.has("kind") || q.getAll("kind").includes(s.kind)) &&
          (!q.has("severity") || q.getAll("severity").includes(s.severity)),
      )
      .sort(
        (a, b) =>
          ({ high: 0, medium: 1, low: 2 })[a.severity] -
          { high: 0, medium: 1, low: 2 }[b.severity],
      );
    return paged(signals, url);
  }),
  http.get("*/api/v1/universities", ({ request }) => {
    const items = scope(request);
    if (!items) return problem("AUTH_REQUIRED", 401, "Нужна авторизация");
    const url = new URL(request.url);
    const search = url.searchParams.get("search")?.toLowerCase() || "";
    return paged(
      universityRows(items).filter((u) =>
        `${u.name} ${u.short_name} ${u.region}`.toLowerCase().includes(search),
      ),
      url,
    );
  }),
  http.get("*/api/v1/universities/:id", ({ request, params }) => {
    const items = scope(request);
    if (!items) return problem("AUTH_REQUIRED", 401, "Нужна авторизация");
    const u = universityRows(items).find((x) => x.id === params.id);
    return u
      ? HttpResponse.json(u)
      : problem("NOT_FOUND", 404, "Вуз недоступен");
  }),
  http.post(
    "*/api/v1/interactions/:id/transitions",
    async ({ request, params }) => {
      const items = scope(request);
      if (!items) return problem("AUTH_REQUIRED", 401, "Нужна авторизация");
      const i = items.find((x) => x.id === params.id);
      if (!i) return problem("NOT_FOUND", 404, "Запись недоступна");
      const body = (await request.json()) as Schema["TransitionCreate"];
      if (body.expected_version !== i.version)
        return problem(
          "INTERACTION_VERSION_CONFLICT",
          409,
          "Взаимодействие уже изменено. Обновите карточку.",
        );
      const target = i.allowed_transitions.find(
        (x) => x.to_stage.id === body.to_stage_id,
      );
      if (!target || i.status !== "active")
        return problem("WF_TRANSITION_NOT_ALLOWED", 409, "Переход недоступен");
      if (target.requires_comment && !body.comment?.trim())
        return problem("WF_COMMENT_REQUIRED", 422, "Добавьте комментарий");
      if ((body.comment?.length || 0) > 4000)
        return problem("VALIDATION_ERROR", 422, "Комментарий слишком длинный");
      if (body.attachment_ids?.length)
        return problem(
          "VALIDATION_ERROR",
          422,
          "Загрузка документов пока недоступна",
        );
      if (target.requires_attachment)
        return problem("WF_ATTACHMENT_REQUIRED", 422, "Нужен документ");
      const transition: Schema["TransitionOut"] = {
        id: crypto.randomUUID(),
        from_stage: i.stage,
        to_stage: target.to_stage,
        actor: { id: user(request)!.id, full_name: user(request)!.full_name },
        occurred_at: new Date().toISOString(),
        comment: body.comment?.trim() || null,
        source: "manual",
      };
      i.stage = target.to_stage;
      i.days_on_stage = 0;
      i.version += 1;
      i.history.unshift(transition);
      i.stage_entered_at = transition.occurred_at;
      i.last_activity_at = transition.occurred_at;
      i.signals = i.signals.filter((s) => s.kind === "license_expiring");
      i.open_signals = i.signals.map(({ kind, severity }) => ({
        kind,
        severity,
      }));
      i.allowed_transitions = allowedFor(
        i.stage.id,
        i.group.code === "b2c" ? mockClientWorkflow : mockWorkflow,
      );
      return HttpResponse.json({ interaction: i, transition }, { status: 201 });
    },
  ),
  unsupportedServiceAction,
];
