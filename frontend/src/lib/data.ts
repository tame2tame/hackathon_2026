export type Role = "kam" | "manager" | "admin";
export const roleNames: Record<Role, string> = {
  kam: "КАМ",
  manager: "Руководитель",
  admin: "Администратор",
};
export const stages = [
  "Поиск контактов",
  "Коммуникация",
  "Встреча",
  "Обмен документами",
  "Доработка документов",
  "Подписание",
  "Передача материалов",
  "Поддержка внедрения",
  "Обучение преподавателей",
  "Обновление программы",
  "Ведение занятий",
  "Обновление документации",
  "Повышение квалификации",
  "Контроль этапов",
];
export const kinds = {
  stage_overdue: "Этап затянулся",
  license_expiring: "Истекает лицензия",
  missing_document: "Нет документа",
  inactivity: "Нет активности",
};
export type Kind = keyof typeof kinds;
export interface Interaction {
  id: string;
  university: string;
  short: string;
  region: string;
  program: string;
  product: string;
  owner: string;
  stage: number;
  days: number;
  kind: Kind;
  evidence: string;
  severity: "high" | "medium" | "low";
  history: { text: string; date: string }[];
}
export const initialData: Interaction[] = [
  {
    id: "int-001",
    university: "МГТУ им. Н. Э. Баумана",
    short: "МГТУ",
    region: "Москва",
    program: "DevOps-инженерия",
    product: "Базис",
    owner: "Анна Смирнова",
    stage: 5,
    days: 41,
    kind: "stage_overdue",
    evidence:
      "41 день на этапе «Подписание» при норме 14 дней. Норма задана вручную.",
    severity: "high",
    history: [],
  },
  {
    id: "int-002",
    university: "Университет ИТМО",
    short: "ИТМО",
    region: "Санкт-Петербург",
    program: "Мобильная разработка",
    product: "ОС Аврора",
    owner: "Анна Смирнова",
    stage: 10,
    days: 8,
    kind: "license_expiring",
    evidence:
      "Лицензия по договору Д-2026/042 истекает 04.10.2026 — через 19 дней на дату демо.",
    severity: "high",
    history: [],
  },
  {
    id: "int-003",
    university: "Уральский федеральный университет",
    short: "УрФУ",
    region: "Екатеринбург",
    program: "Анализ данных",
    product: "Loginom",
    owner: "Михаил Волков",
    stage: 6,
    days: 6,
    kind: "missing_document",
    evidence:
      "На этапе «Передача материалов» отсутствует обязательный акт передачи.",
    severity: "medium",
    history: [],
  },
  {
    id: "int-004",
    university: "Казанский федеральный университет",
    short: "КФУ",
    region: "Казань",
    program: "Веб-разработка",
    product: "Акола",
    owner: "Анна Смирнова",
    stage: 2,
    days: 23,
    kind: "inactivity",
    evidence:
      "Последнее действие — встреча 23.08.2026. Нет активности 23 дня, порог — 21 день.",
    severity: "low",
    history: [],
  },
  {
    id: "int-005",
    university: "Новосибирский государственный университет",
    short: "НГУ",
    region: "Новосибирск",
    program: "DevOps-инженерия",
    product: "Базис",
    owner: "Михаил Волков",
    stage: 3,
    days: 18,
    kind: "stage_overdue",
    evidence:
      "18 дней на этапе «Обмен документами» при норме 14 дней. Норма задана вручную.",
    severity: "medium",
    history: [],
  },
  {
    id: "int-006",
    university: "Санкт-Петербургский политехнический университет",
    short: "СПбПУ",
    region: "Санкт-Петербург",
    program: "Мобильная разработка",
    product: "ОС Аврора",
    owner: "Анна Смирнова",
    stage: 8,
    days: 12,
    kind: "license_expiring",
    evidence:
      "Лицензия по договору Д-2026/068 истекает 29.10.2026 — через 44 дня на дату демо.",
    severity: "medium",
    history: [],
  },
];
export function visibleData(data: Interaction[], role: Role) {
  return role === "kam"
    ? data.filter((i) => i.owner === "Анна Смирнова")
    : data;
}
export function hasSignal(i: Interaction) {
  return !(i.kind === "stage_overdue" && i.days === 0);
}
export function advance(data: Interaction[], id: string, comment: string) {
  if (!comment.trim()) throw new Error("COMMENT_REQUIRED");
  return data.map((i) =>
    i.id === id && i.stage < 13
      ? {
          ...i,
          stage: i.stage + 1,
          days: 0,
          history: [
            {
              text: `${stages[i.stage]} → ${stages[i.stage + 1]}. ${comment.trim()}`,
              date: new Date().toLocaleString("ru-RU"),
            },
            ...i.history,
          ],
        }
      : i,
  );
}
