import type { Schema } from "../api/types";
export const palette = [
  "#7700ff",
  "#ff4f12",
  "#179b91",
  "#a16ae8",
  "#d39522",
  "#4e83c4",
];
export const number = (n: number) =>
  n.toLocaleString("ru-RU", { maximumFractionDigits: 1 });
export function slices(chart: Schema["ChartOut"]) {
  const total = chart.values.reduce((s, v) => s + v, 0);
  let offset = 0;
  return chart.labels
    .map((label, index) => {
      const value = chart.values[index] || 0;
      const share = total ? value / total : 0;
      const result = { label, index, value, share, offset };
      offset += share;
      return result;
    })
    .filter((s) => s.value > 0);
}
// A completed visit ends at the next transition, including return visits.
export function completedVisits(
  records: Pick<Schema["InteractionDetail"], "history">[],
) {
  return records.flatMap((r) => {
    const history = [...r.history].sort(
      (a, b) => Date.parse(a.occurred_at) - Date.parse(b.occurred_at),
    );
    return history
      .slice(0, -1)
      .map((t, i) => ({
        stage: t.to_stage.name,
        code: t.to_stage.code,
        at: history[i + 1].occurred_at,
        days: Math.floor(
          (Date.parse(history[i + 1].occurred_at) - Date.parse(t.occurred_at)) /
            86400000,
        ),
      }));
  });
}
export function durationChart(
  records: Pick<Schema["InteractionDetail"], "history">[],
  stages: { name: string }[],
): Schema["ChartOut"] {
  const visits = completedVisits(records);
  const rows = stages
    .map((s) => ({
      label: s.name,
      values: visits.filter((v) => v.stage === s.name).map((v) => v.days),
    }))
    .filter((r) => r.values.length);
  return {
    title: "Средняя длительность этапа, дней",
    labels: rows.map((r) => r.label),
    values: rows.map((r) =>
      Math.round(r.values.reduce((a, b) => a + b, 0) / r.values.length),
    ),
    option: {},
  };
}
export function timeline(
  records: Pick<Schema["InteractionDetail"], "history">[],
  days: number,
  metric: "transitions" | "duration",
  stage = "",
  now = new Date(),
) {
  const end = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1),
  );
  const start = new Date(end.getTime() - days * 86400000);
  const step = days <= 30 ? 1 : 7;
  const bins = Array.from({ length: Math.ceil(days / step) }, (_, i) => ({
    date: new Date(start.getTime() + i * step * 86400000),
    values: [] as number[],
  }));
  const events =
    metric === "duration"
      ? completedVisits(records)
          .filter((v) => !stage || v.code === stage)
          .map((v) => ({ at: v.at, value: v.days }))
      : records.flatMap((r) =>
          r.history
            .filter(
              (t) => t.from_stage && (!stage || t.to_stage.code === stage),
            )
            .map((t) => ({ at: t.occurred_at, value: 1 })),
        );
  for (const e of events) {
    const idx = Math.floor(
      (Date.parse(e.at) - start.getTime()) / (step * 86400000),
    );
    if (idx >= 0 && idx < bins.length && Date.parse(e.at) < end.getTime())
      bins[idx].values.push(e.value);
  }
  return {
    labels: bins.map((b) => b.date.toISOString().slice(0, 10)),
    values: bins.map((b) =>
      b.values.length
        ? metric === "duration"
          ? b.values.reduce((a, v) => a + v, 0) / b.values.length
          : b.values.length
        : metric === "duration"
          ? null
          : 0,
    ),
    samples: bins.map((b) => b.values.length),
    step,
  };
}
