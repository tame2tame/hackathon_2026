import { initialData, stages } from "../lib/data";
import type { Interaction, Me, Schema, Workflow } from "../api/types";
export const uid = (n: number) =>
  `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const codes = [
  "contact_search",
  "communication",
  "meeting",
  "documents_exchange",
  "documents_revision",
  "signing",
  "materials_transfer",
  "implementation_support",
  "teacher_training",
  "curriculum_update",
  "classes",
  "docs_update",
  "teacher_upskilling",
  "stage_control",
];
const norms = [14, 21, 30, 14, 10, 14, 14, 30, 30, 30, 120, 30, 60, null];
export const mockUsers: Me[] = [
  {
    id: uid(1),
    full_name: "Анна Смирнова",
    email: "anna.smirnova@example.com",
    role: "kam",
    scope: "own",
    team: { id: uid(10), name: "Команда вузов" },
  },
  {
    id: uid(2),
    full_name: "Михаил Волков",
    email: "mikhail.volkov@example.com",
    role: "kam",
    scope: "own",
    team: { id: uid(10), name: "Команда вузов" },
  },
  {
    id: uid(3),
    full_name: "Роман Ковалёв",
    email: "roman.kovalev@example.com",
    role: "manager",
    scope: "team",
    team: { id: uid(10), name: "Команда вузов" },
  },
  {
    id: uid(4),
    full_name: "Алина Денисова",
    email: "alina.denisova@example.com",
    role: "admin",
    scope: "all",
    team: null,
  },
];
export const mockWorkflow: Workflow = {
  id: uid(20),
  template_id: uid(21),
  name: "Базовый путь взаимодействия",
  version_no: 1,
  stages: stages.map((name, i) => ({
    id: uid(100 + i),
    code: codes[i],
    name,
    position: i + 1,
    kind: i === 0 ? "start" : i === 13 ? "final" : "normal",
    bulk_allowed: i < 6,
    required_document_types:
      i === 5
        ? ["signed_contract"]
        : i === 6
          ? ["transfer_act"]
          : i === 8
            ? ["training_confirmation"]
            : [],
    norm_days: norms[i],
  })),
  transitions: [],
};
// Возвраты разрешены с комментарием и без документа.
mockWorkflow.transitions = [
  ...codes
    .slice(1)
    .map((_, i) => ({
      from_stage_id: uid(101 + i),
      to_stage_id: uid(100 + i),
      requires_comment: true,
      requires_attachment: false,
    })),
  ...codes.slice(0, -1).map((_, i) => ({
    from_stage_id: uid(100 + i),
    to_stage_id: uid(101 + i),
    requires_comment: true,
    requires_attachment: false,
  })),
  {
    from_stage_id: uid(103),
    to_stage_id: uid(105),
    requires_comment: true,
    requires_attachment: false,
  },
];
export function allowedFor(
  stageId: string,
  workflow: Workflow = mockWorkflow,
): Interaction["allowed_transitions"] {
  return workflow.transitions
    .filter((r) => r.from_stage_id === stageId)
    .map((r) => ({
      to_stage: workflow.stages.find((s) => s.id === r.to_stage_id)!,
      requires_comment: r.requires_comment,
      requires_attachment: r.requires_attachment,
    }));
}
export const mockGroups: Schema["CounterpartyGroupOut"][] = [
  {
    id: uid(30),
    code: "b2b",
    name: "Вузы (B2B)",
    description: null,
    workflow_template_id: uid(21),
    position: 0,
  },
  {
    id: uid(31),
    code: "b2c",
    name: "Частные лица (B2C)",
    description: null,
    workflow_template_id: uid(22),
    position: 1,
  },
];
export const mockClientWorkflow: Workflow = {
  id: uid(23),
  template_id: uid(22),
  name: "Обучение клиентов",
  version_no: 1,
  stages: [
    {
      ...mockWorkflow.stages[0],
      id: uid(910),
      code: "application",
      name: "Заявка",
    },
    {
      ...mockWorkflow.stages[1],
      id: uid(911),
      code: "enrollment",
      name: "Зачисление",
    },
  ],
  transitions: [],
};
mockClientWorkflow.transitions = [
  {
    from_stage_id: uid(910),
    to_stage_id: uid(911),
    requires_comment: true,
    requires_attachment: false,
  },
  {
    from_stage_id: uid(911),
    to_stage_id: uid(910),
    requires_comment: true,
    requires_attachment: false,
  },
];
const time = "2026-09-16T09:00:00Z";
export function createFixtures(): Interaction[] {
  const universities: Interaction[] = initialData.map((i, n) => {
    const owner = mockUsers[i.owner === "Анна Смирнова" ? 0 : 1];
    const stage = mockWorkflow.stages[i.stage];
    const signal: Schema["SignalOut"] = {
      id: uid(500 + n),
      kind: i.kind,
      severity: i.severity,
      detected_at: time,
      resolved_at: null,
      message:
        i.kind === "inactivity"
          ? "Нет активности 23 дня, порог составляет 14 дней."
          : i.evidence,
      evidence: {
        stage_code: stage.code,
        days_on_stage: i.days,
        norm_days: stage.norm_days,
      },
    };
    const signals = [signal];
    if (n === 0)
      signals.push({
        id: uid(510),
        kind: "missing_document",
        severity: "medium",
        detected_at: time,
        resolved_at: null,
        message: "На этапе «Подписание» нет подписанного договора.",
        evidence: { missing_document_types: ["signed_contract"] },
      });
    return {
      id: uid(200 + n),
      group: mockGroups[0],
      counterparty: {
        id: uid(300 + n),
        kind: "university",
        name: i.university,
        short_name: i.short,
      },
      client: null,
      university: {
        id: uid(300 + n),
        name: i.university,
        short_name: i.short,
        region: i.region,
      },
      program: {
        id: uid(400 + n),
        name: i.program,
        priority: 0,
        direction: {
          id: uid(450 + n),
          name: i.program,
          code: "direction-" + n,
        },
      },
      product: {
        id: uid(600 + n),
        name: i.product,
        vendor: { id: uid(650 + n), name: i.product },
      },
      owner: { id: owner.id, full_name: owner.full_name },
      stage,
      stage_entered_at: time,
      days_on_stage: i.days,
      norm_days: stage.norm_days,
      status: "active",
      version: 1,
      last_activity_at: time,
      open_signals: signals.map(({ kind, severity }) => ({ kind, severity })),
      workflow_version_id: mockWorkflow.id,
      contract: null,
      history: [
        {
          id: uid(700 + n),
          from_stage: null,
          to_stage: stage,
          occurred_at: time,
          actor: { id: owner.id, full_name: owner.full_name },
          comment: "Начальное состояние демонстрации",
          source: "demo",
        },
      ],
      allowed_transitions: allowedFor(stage.id),
      signals,
    };
  });
  const client: Interaction = {
    ...universities[0],
    id: uid(290),
    group: mockGroups[1],
    counterparty: {
      id: uid(900),
      kind: "person",
      name: "Демо Клиент",
      short_name: "Демо Клиент",
    },
    client: { id: uid(900), kind: "person", name: "Демо Клиент" },
    university: null,
    product: null,
    owner: { id: mockUsers[1].id, full_name: mockUsers[1].full_name },
    program: {
      ...universities[0].program,
      id: uid(490),
      name: "Управление проектами",
    },
    stage: mockClientWorkflow.stages[0],
    workflow_version_id: mockClientWorkflow.id,
    days_on_stage: 16,
    norm_days: 14,
    allowed_transitions: allowedFor(uid(910), mockClientWorkflow),
    contract: null,
    history: [],
    signals: [
      {
        ...universities[0].signals[0],
        id: uid(590),
        kind: "inactivity",
        message: "Нет активности 16 дней, порог составляет 14 дней.",
        evidence: { idle_days: 16, threshold_days: 14 },
      },
    ],
    open_signals: [{ kind: "inactivity", severity: "high" }],
  };
  return [...universities, client];
}
