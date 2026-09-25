import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, BarChart3 } from "lucide-react";
import { api } from "../api/runtime";
import type { Schema } from "../api/types";
import { Select } from "../components/ui/select";
import { Field, State } from "./shared";
import { number, timeline } from "./analytics-data";
export function ProcessTimeline({ group }: { group: string }) {
  const [days, setDays] = useState(90);
  const [metric, setMetric] = useState<"transitions" | "duration">(
    "transitions",
  );
  const [stage, setStage] = useState("");
  const [view, setView] = useState("line");
  const [active, setActive] = useState<number | null>(null);
  const q = useQuery({
    queryKey: ["service", "process-history", group],
    enabled: !!group,
    staleTime: 60000,
    queryFn: async ({ signal }) => {
      const items: Schema["InteractionListItem"][] = [];
      for (let page = 1; ; page++) {
        const batch = await api.get<Schema["Page_InteractionListItem_"]>(
          "/interactions",
          { group_id: group, page, page_size: 100 },
          signal,
        );
        if (batch.total > 1000)
          throw Error(
            "В группе больше 1000 записей. Для динамики такой выборки нужен агрегированный отчёт сервера; текущие срезы доступны выше.",
          );
        items.push(...batch.items);
        if (items.length >= batch.total) break;
        if (!batch.items.length)
          throw Error("Состав выборки изменился. Обновите динамику.");
      }
      const result: Schema["InteractionDetail"][] = [];
      // Limit concurrent detail requests; cancel the whole selection when the group changes.
      for (let i = 0; i < items.length; i += 4)
        result.push(
          ...(await Promise.all(
            items.slice(i, i + 4).map((r) => api.interaction(r.id, signal)),
          )),
        );
      return result;
    },
  });
  const records = q.data || [];
  const stages = [
    ...new Map(
      records
        .flatMap((r) =>
          r.history.flatMap((t) => [
            t.to_stage,
            ...(t.from_stage ? [t.from_stage] : []),
          ]),
        )
        .map((s) => [s.code, s]),
    ).values(),
  ];
  const data = timeline(records, days, metric, stage);
  const max = Math.max(1, ...data.values.map((v) => v ?? 0));
  const x = (i: number) => 48 + (i * 680) / Math.max(1, data.values.length - 1);
  const y = (v: number) => 210 - (v / max) * 170;
  const path = data.values
    .map((v, i) =>
      v === null
        ? ""
        : `${i === 0 || data.values[i - 1] === null ? "M" : "L"}${x(i)},${y(v)}`,
    )
    .join(" ");
  const selected = active !== null ? data.values[active] : null;
  return (
    <>
      <div className="timeline-filters">
        <Field label="Показатель">
          <Select
            value={metric}
            onChange={(e) => {
              setMetric(e.target.value as typeof metric);
              setActive(null);
            }}
          >
            <option value="transitions">Переходы между этапами</option>
            <option value="duration">Длительность завершённых этапов</option>
          </Select>
        </Field>
        <Field label="Период">
          <Select
            value={days}
            onChange={(e) => {
              setDays(Number(e.target.value));
              setActive(null);
            }}
          >
            <option value="30">Последние 30 дней</option>
            <option value="90">Последние 90 дней</option>
            <option value="180">Последние 180 дней</option>
          </Select>
        </Field>
        <Field label="Этап">
          <Select value={stage} onChange={(e) => setStage(e.target.value)}>
            <option value="">Все этапы</option>
            {stages.map((s) => (
              <option key={s.code} value={s.code}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <State query={q}>
        <div className="chart-controls">
          <div
            className="chart-type-control"
            role="group"
            aria-label="Вид динамики"
          >
            <button
              aria-pressed={view === "line"}
              onClick={() => setView("line")}
            >
              <TrendingUp size={15} />
              Динамика
            </button>
            <button
              aria-pressed={view === "bar"}
              onClick={() => setView("bar")}
            >
              <BarChart3 size={15} />
              Столбчатый
            </button>
          </div>
          <span className="chart-hint">
            {data.step === 1 ? "По дням" : "По 7 дней"} · UTC
          </span>
        </div>
        <p className="timeline-readout" aria-live="polite">
          {active !== null
            ? `${data.labels[active]}${data.step > 1 ? " · начало интервала" : ""}: ${selected === null ? "нет наблюдений" : number(selected) + (metric === "duration" ? ` дн. · ${data.samples[active]} завершённых этапов` : " переходов")}`
            : "Наведите на точку или выберите интервал в таблице"}
        </p>
        <svg
          className="timeline-svg"
          viewBox="0 0 760 250"
          role="img"
          aria-label={
            metric === "duration"
              ? "Средняя длительность завершённых этапов по дате выхода"
              : "Количество переходов по времени"
          }
        >
          {[0, 0.25, 0.5, 0.75, 1].map((v) => (
            <g key={v}>
              <line
                x1="48"
                x2="728"
                y1={y(v * max)}
                y2={y(v * max)}
                stroke="#e8e6ef"
              />
              <text
                x="37"
                y={y(v * max) + 4}
                textAnchor="end"
                fill="#72798a"
                fontSize="11"
              >
                {number(v * max)}
              </text>
            </g>
          ))}
          {view === "line" && (
            <path d={path} fill="none" stroke="#7700ff" strokeWidth="3" />
          )}
          {data.values.map((v, i) =>
            v === null ? null : (
              <g
                key={i}
                onMouseEnter={() => setActive(i)}
                onClick={() => setActive(i)}
              >
                {view === "bar" ? (
                  <rect
                    x={x(i) - 5}
                    y={y(v)}
                    width="10"
                    height={210 - y(v)}
                    rx="3"
                    fill="#7700ff"
                  />
                ) : (
                  <circle
                    cx={x(i)}
                    cy={y(v)}
                    r={active === i ? 6 : 3.5}
                    fill={active === i ? "#ff4f12" : "#7700ff"}
                  />
                )}
                <circle cx={x(i)} cy={y(v)} r="12" fill="transparent">
                  <title>
                    {data.labels[i]}: {number(v)}
                  </title>
                </circle>
              </g>
            ),
          )}
          {[
            0,
            Math.floor((data.labels.length - 1) / 2),
            data.labels.length - 1,
          ].map((i) => (
            <text
              key={i}
              x={x(i)}
              y="239"
              textAnchor={
                i === 0
                  ? "start"
                  : i === data.labels.length - 1
                    ? "end"
                    : "middle"
              }
              fill="#72798a"
              fontSize="11"
            >
              {data.labels[i]}
            </text>
          ))}
        </svg>
        {!data.samples.some(Boolean) && (
          <p className="service-empty">
            За этот период подходящих переходов нет.
          </p>
        )}
        <p className="chart-hint">
          По истории {records.length} доступных записей.{" "}
          {metric === "duration"
            ? "Среднее по завершённым посещениям этапа, отнесённое к дате выхода. Пропуски означают отсутствие наблюдений."
            : "Учитываются переходы в выбранный этап, включая возвраты. Первичное создание записи не учитывается."}
        </p>
        <details className="chart-data">
          <summary>Данные по датам</summary>
          <table>
            <thead>
              <tr>
                <th>Начало интервала</th>
                <th>{metric === "duration" ? "Среднее, дней" : "Переходы"}</th>
              </tr>
            </thead>
            <tbody>
              {data.labels.map((l, i) => (
                <tr key={l}>
                  <td>
                    <button onClick={() => setActive(i)}>{l}</button>
                  </td>
                  <td>
                    {data.values[i] === null
                      ? "Нет наблюдений"
                      : number(data.values[i]!)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      </State>
    </>
  );
}
