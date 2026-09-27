import { durationChart } from "../pages/analytics-data";
import { mockStatsReport } from "./stats-report";
import { http, HttpResponse } from "msw";
import {
  createFixtures,
  mockGroups,
  mockUsers,
  mockWorkflow,
  mockClientWorkflow,
  uid,
} from "./fixtures";
import type { Schema } from "../api/types";
const records = createFixtures();
let currentRecords = () => records;
export function setServiceRecordsSource(source: () => typeof records) {
  currentRecords = source;
}
const unique = <T extends { id: string }>(items: T[]) => [
  ...new Map(items.map((i) => [i.id, i])).values(),
];
const programs = unique(records.map((r) => r.program));
const directions = unique(programs.map((p) => p.direction));
const products = unique(records.flatMap((r) => (r.product ? [r.product] : [])));
const now = () => new Date().toISOString();
const jobs: Schema["ReportJobOut"][] = [];
const views: Schema["SavedViewOut"][] = [];
const notes: Record<string, Schema["NoteOut"][]> = {};
const attachments: Record<string, Schema["AttachmentOut"][]> = {};
const ok = <T>(data: T) =>
  new HttpResponse(JSON.stringify(data), {
    headers: { "Content-Type": "application/json" },
  });
const lists: Record<string, unknown> = {
  "/directions": directions,
  "/programs": programs,
  "/products": products,
  "/workflows": [
    {
      id: mockWorkflow.template_id,
      name: mockWorkflow.name,
      is_default: true,
      published_version_id: mockWorkflow.id,
      version_no: 1,
      draft_version_id: null,
      groups: mockGroups,
    },
  ],
  "/admin/users": mockUsers.map((u) => ({
    ...u,
    team_id: u.team?.id || null,
    is_active: true,
  })),
  "/admin/teams": [
    { id: uid(10), name: "Команда вузов", manager_user_id: uid(3) },
  ],
  "/admin/access-rules": [],
  "/admin/settings": [
    {
      key: "radar_thresholds",
      description: "Пороги радара",
      value: {
        license_warn_days: 60,
        license_critical_days: 30,
        inactivity_low_days: 14,
        inactivity_medium_days: 28,
      },
      is_default: true,
      updated_at: null,
    },
  ],
  "/admin/audit": [
    {
      id: 1,
      occurred_at: now(),
      actor_user_id: uid(3),
      action: "interaction.transition",
      entity_kind: "interaction",
      entity_id: records[0].id,
      before: { stage: "Переговоры" },
      after: { stage: "Подписание" },
      trace_id: "demo-audit",
    },
  ],
  "/integrations": [
    {
      id: uid(800),
      name: "Образовательная платформа LMS",
      kind: "lms",
      base_url: "https://lms.example.com",
      is_mock: true,
      schedule_cron: "Каждый час",
      last_sync_at: now(),
      push_enabled: true,
      last_push_at: now(),
    },
    {
      id: uid(801),
      name: "Сайт ИТ Школы",
      kind: "site",
      base_url: "https://school.example.com",
      is_mock: true,
      schedule_cron: "Каждые 15 минут",
      last_sync_at: now(),
      push_enabled: true,
      last_push_at: now(),
    },
  ],
  "/site-applications": [],
  "/import-profiles": [],
  "/notifications": { items: [], total: 0, page: 1, page_size: 20 },
  "/messages": { items: [], unread_total: 0 },
  "/help": [
    {
      slug: "start",
      title: "Начало работы",
      summary: "Как устроено рабочее пространство",
    },
    {
      slug: "interactions",
      title: "Взаимодействия",
      summary: "Этапы, документы, заметки и участники",
    },
  ],
  "/clients": { items: [], total: 0, page: 1, page_size: 100 },
};
const addresses = new Map<string, Schema["AddressOut"][]>();
function userAddresses(request: Request) {
  const user = mockUsers.find(
    (u) => u.email === request.headers.get("X-Dev-User"),
  );
  if (!user) return null;
  if (!addresses.has(user.id))
    addresses.set(
      user.id,
      (["telegram", "max", "email"] as const).map((k) => ({
        channel_kind: k,
        channel_name:
          k === "email"
            ? "Электронная почта"
            : k === "max"
              ? "Max"
              : "Telegram",
        channel_enabled: true,
        address: null,
        is_enabled: false,
      })),
    );
  return addresses.get(user.id)!;
}
function statsCharts(request: Request) {
  const user = mockUsers.find(
    (u) => u.email === request.headers.get("X-Dev-User"),
  );
  if (!user) return null;
  const groupId = new URL(request.url).searchParams.get("group_id");
  const group = mockGroups.find((g) => g.id === (groupId || mockGroups[0].id));
  if (!group) return null;
  const workflow =
    group.id === mockGroups[0].id ? mockWorkflow : mockClientWorkflow;
  const visible = currentRecords().filter(
    (r) =>
      (user.role !== "kam" || r.owner.id === user.id) &&
      r.group.id === group.id,
  );
  const byDirection = new Map<string, number>();
  for (const r of currentRecords().filter(
    (r) =>
      (user.role !== "kam" || r.owner.id === user.id) &&
      (!groupId || r.group.id === groupId) &&
      r.status !== "cancelled",
  ))
    byDirection.set(
      r.program.direction.name,
      (byDirection.get(r.program.direction.name) || 0) + 1,
    );
  const rows = [...byDirection].sort((a, b) => b[1] - a[1]);
  return {
    group,
    charts: [
      {
        title: "Взаимодействия по этапам",
        labels: workflow.stages.map((s) => s.name),
        values: workflow.stages.map(
          (s) => visible.filter((r) => r.stage.code === s.code).length,
        ),
        option: {},
      },
      durationChart(visible, workflow.stages),
      {
        title: "Взаимодействия по направлениям",
        labels: rows.map((r) => r[0]),
        values: rows.map((r) => r[1]),
        option: {},
      },
    ],
  };
}
export const serviceHandlers = [
  ...Object.entries(lists).map(([path, data]) =>
    http.get("*/api/v1" + path, () => ok(data)),
  ),
  http.get("*/api/v1/me/notification-addresses", ({ request }) => {
    const data = userAddresses(request);
    return data ? ok(data) : new HttpResponse(null, { status: 401 });
  }),
  http.put(
    "*/api/v1/me/notification-addresses/:kind",
    async ({ request, params }) => {
      const item = userAddresses(request)?.find(
        (a) => a.channel_kind === params.kind,
      );
      if (!item) return new HttpResponse(null, { status: 404 });
      const body = (await request.json()) as Schema["AddressUpdate"];
      if (
        !body.address?.trim() ||
        body.address.length > 254 ||
        typeof body.is_enabled !== "boolean"
      )
        return new HttpResponse(null, { status: 422 });
      item.address = body.address.trim();
      item.is_enabled = body.is_enabled;
      return ok(item);
    },
  ),
  http.get("*/api/v1/analytics/stats/report", async ({ request }) => {
    const data = statsCharts(request);
    if (!data) return new HttpResponse(null, { status: 404 });
    const pdf = await mockStatsReport(data.charts, data.group.name);
    return new HttpResponse(pdf.buffer as ArrayBuffer, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": 'attachment; filename="statistics.pdf"',
      },
    });
  }),
  http.get("*/api/v1/analytics/stats/:kind", ({ request, params }) => {
    const index = ["funnel", "stage-durations", "distribution"].indexOf(
      String(params.kind),
    );
    const data = statsCharts(request);
    return data && index >= 0
      ? ok(data.charts[index])
      : new HttpResponse(null, { status: 404 });
  }),
  http.get("*/api/v1/analytics/rating", ({ request }) => {
    const query = new URL(request.url).searchParams;
    const entity =
      query.get("entity") === "university" ? "university" : "program";
    const weights = {
      applications: Number(query.get("w_applications") || 40),
      students: Number(query.get("w_students") || 40),
      streams: Number(query.get("w_streams") || 20),
    };
    return ok({
      entity,
      weights,
      order: "score",
      rows: programs.map((p, i) => ({
        place: i + 1,
        place_change: i === 0 ? 2 : null,
        id: p.id,
        name:
          entity === "program"
            ? p.name
            : records[i % records.length].counterparty.name,
        direction_name: p.direction.name,
        score: 92 - i * 9,
        priority: 0,
        contributions: Object.entries(weights).map(([metric, weight]) => ({
          metric,
          weight,
          value: 120 - i * 10,
          normalized: 92 - i * 9,
          contribution: (weight * (92 - i * 9)) / 100,
        })),
        complete: i !== 2,
        missing_metrics: i === 2 ? ["streams"] : [],
      })),
    } satisfies Schema["RatingOut"]);
  }),
  http.get("*/api/v1/reports", () => ok(jobs)),
  http.post("*/api/v1/reports", async ({ request }) => {
    const body = (await request.json()) as Schema["ReportCreate"];
    const job: Schema["ReportJobOut"] = {
      id: uid(900 + jobs.length),
      status: "done",
      format: body.format,
      progress: 100,
      row_count: records.length,
      error_code: null,
      created_at: now(),
      finished_at: now(),
    };
    jobs.unshift(job);
    return HttpResponse.json(job, { status: 202 });
  }),
  http.get("*/api/v1/signals/summary", () =>
    ok({
      kinds: [
        "stage_overdue",
        "license_expiring",
        "missing_document",
        "inactivity",
      ],
      rows: mockUsers.slice(0, 2).map((u) => ({
        owner: u,
        counts: {
          stage_overdue: 3,
          license_expiring: 1,
          missing_document: 2,
          inactivity: 1,
        },
        total: 7,
      })),
      total: 14,
    } satisfies Schema["SignalSummaryOut"]),
  ),
  http.get("*/api/v1/workflows/:id/norms", () =>
    ok(
      mockWorkflow.stages
        .filter((s) => s.norm_days)
        .map(
          (s) =>
            ({
              stage_code: s.code,
              stage_name: s.name,
              norm_days: s.norm_days!,
              source: "manual",
              suggested_median_days: 10,
              suggested_percentile_days: 14,
              sample_size: 25,
            }) satisfies Schema["StageNormOut"],
        ),
    ),
  ),
  http.get("*/api/v1/integrations/:id/runs", ({ params }) =>
    ok([
      {
        id: uid(850),
        source_id: String(params.id),
        direction: "pull",
        started_at: now(),
        finished_at: now(),
        status: "done",
        stats: { updated: 12 },
        error_code: null,
      },
    ] satisfies Schema["SyncRunOut"][]),
  ),
  http.get("*/api/v1/integrations/:id/outbox", () => ok([])),
  http.get("*/api/v1/interactions/:id/notes", ({ params }) =>
    ok(notes[String(params.id)] || []),
  ),
  http.post("*/api/v1/interactions/:id/notes", async ({ params, request }) => {
    const { text } = (await request.json()) as Schema["NoteCreate"];
    const n = {
      id: crypto.randomUUID(),
      text,
      author: mockUsers[0],
      created_at: now(),
    };
    (notes[String(params.id)] ??= []).push(n);
    return ok(n);
  }),
  http.get("*/api/v1/interactions/:id/attachments", ({ params }) =>
    ok(attachments[String(params.id)] || []),
  ),
  http.get("*/api/v1/interactions/:id/participants", () =>
    ok({
      counts: { students: 0, teachers: 0 },
      items: [],
    } satisfies Schema["ParticipantsOut"]),
  ),
  http.get("*/api/v1/universities/:id/contacts", () => ok([])),
  http.get("*/api/v1/saved-views", ({ request }) =>
    ok(
      views.filter(
        (v) => v.page === new URL(request.url).searchParams.get("page"),
      ),
    ),
  ),
  http.post("*/api/v1/saved-views", async ({ request }) => {
    const body = (await request.json()) as Schema["SavedViewCreate"];
    const view: Schema["SavedViewOut"] = {
      ...body,
      id: crypto.randomUUID(),
      filters: body.filters || {},
      columns: body.columns || [],
      updated_at: now(),
    };
    views.push(view);
    return ok(view);
  }),
  http.get("*/api/v1/help/:slug", ({ params }) =>
    ok({
      slug: String(params.slug),
      title: "Руководство пользователя",
      summary: "Работа с сервисом",
      body: "# Радар вузов\nВыберите сигнал на главной странице, чтобы перейти к взаимодействию.\n## Документы и этапы\nЗагрузите документ и добавьте комментарий перед переходом.",
    } satisfies Schema["HelpTopicOut"]),
  ),
];
// Демо не должно выдавать непроверенную мутацию за сохранение на настоящем сервере.
export const unsupportedServiceAction = http.all("*/api/v1/*", () =>
  HttpResponse.json(
    {
      type: "about:blank",
      title: "Для этого действия подключите API",
      detail:
        "В автономном демо это действие не имитируется. Переключите VITE_AUTH_MODE на dev или keycloak для работы с сервером.",
      status: 501,
      code: "INTERNAL_ERROR",
      trace_id: "demo-only",
      errors: [],
    },
    { status: 501 },
  ),
);
