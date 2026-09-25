import { ChartView } from "./Charts";
import { ProcessTimeline } from "./ProcessTimeline";
import { number } from "./analytics-data";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Heading } from "../App";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
import { api } from "../api/runtime";
import type { Me, Schema } from "../api/types";
import {
  Download,
  EmptyData,
  Failure,
  Field,
  Panel,
  State,
  names,
  useAction,
  useResource,
} from "./shared";
export { Bars } from "./Charts";
export function StatsPage() {
  const [chosen, setChosen] = useState("");
  const [tab, setTab] = useState("overview");
  const groups = useResource<Schema["CounterpartyGroupOut"][]>(
    "/counterparty-groups",
  );
  const group = chosen || groups.data?.[0]?.id || "";
  const funnel = useResource<Schema["ChartOut"]>(
    "/analytics/stats/funnel",
    { group_id: group },
    !!group,
  );
  const duration = useResource<Schema["ChartOut"]>(
    "/analytics/stats/stage-durations",
    { group_id: group },
    !!group,
  );
  const distribution = useResource<Schema["ChartOut"]>(
    "/analytics/stats/distribution",
    { group_id: group },
    !!group,
  );
  const workflow = useResource<Schema["WorkflowOut"]>(
    `/workflows/${groups.data?.find((g) => g.id === group)?.workflow_template_id}`,
    {},
    !!group,
  );
  const navigate = useNavigate();
  const count = funnel.data?.values.reduce((a, b) => a + b, 0);
  const occupied = funnel.data?.values.filter((v) => v > 0).length;
  const slow = duration.data?.values.length
    ? duration.data.values.indexOf(Math.max(...duration.data.values))
    : -1;
  const peak = funnel.data?.values.some(Boolean)
    ? funnel.data.values.indexOf(Math.max(...funnel.data.values))
    : -1;
  const [focus, setFocus] = useState<number | null>(null);
  useEffect(() => setFocus(null), [group]);
  return (
    <>
      <Heading
        eyebrow="АНАЛИТИКА ПРОЦЕССОВ"
        title="Статистика"
        text="От общей картины — к этапам, которые требуют внимания."
      />
      <div className="dashboard-toolbar">
        <Field label="Процесс / группа контрагентов">
          <Select value={group} onChange={(e) => setChosen(e.target.value)}>
            {!groups.data && <option value="">Загрузка групп…</option>}
            {groups.data?.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </Select>
        </Field>
        <div className="dashboard-scope">
          <i />
          Актуальный срез доступных вам записей
        </div>
        {group && (
          <Download
            path={`/analytics/stats/report?group_id=${group}`}
            name="Статистика.pdf"
          >
            Скачать PDF
          </Download>
        )}
      </div>
      <Failure error={groups.error} />
      <div className="analytics-kpis">
        <article>
          <span>Записей на этапах</span>
          <strong>{count === undefined ? "—" : number(count)}</strong>
          <small>Текущий срез выбранного процесса</small>
        </article>
        <article>
          <span>Этапов с записями</span>
          <strong>
            {occupied ?? "—"}
            <em> / {funnel.data?.labels.length ?? "—"}</em>
          </strong>
          <small>Распределение рабочей нагрузки</small>
        </article>
        <article>
          <span>Больше всего записей</span>
          <strong>{peak >= 0 ? number(funnel.data!.values[peak]) : "—"}</strong>
          <small>
            {peak >= 0 ? funnel.data!.labels[peak] : "Пока нет наблюдений"}
          </small>
        </article>
        <article>
          <span>Самый долгий этап</span>
          <strong>
            {slow >= 0 ? number(duration.data!.values[slow]) : "—"}
            <em> дн.</em>
          </strong>
          <small>
            {slow >= 0 ? duration.data!.labels[slow] : "Нет завершённых этапов"}
          </small>
        </article>
      </div>
      <div
        className="dashboard-tabs"
        role="group"
        aria-label="Раздел статистики"
      >
        <button
          aria-pressed={tab === "overview"}
          onClick={() => setTab("overview")}
        >
          Обзор процессов
        </button>
        <button
          aria-pressed={tab === "timeline"}
          onClick={() => setTab("timeline")}
        >
          Динамика во времени
        </button>
      </div>
      {tab === "timeline" ? (
        <Panel title="Как меняется процесс">
          <ProcessTimeline key={group} group={group} />
        </Panel>
      ) : (
        <>
          <div className="analytics-grid dashboard-charts">
            <Panel title="Распределение по этапам">
              <p className="chart-hint">
                Текущее число записей, а не конверсия. Нажмите на этап для
                детализации.
              </p>
              <State query={funnel}>
                {funnel.data && (
                  <ChartView chart={funnel.data} onPick={setFocus} />
                )}
              </State>
              {focus !== null && funnel.data && (
                <div className="chart-selection" role="status">
                  <div>
                    <strong>{funnel.data.labels[focus]}</strong>
                    <span>
                      {number(funnel.data.values[focus])} записей ·{" "}
                      {count
                        ? number((funnel.data.values[focus] / count) * 100)
                        : 0}
                      % от среза
                    </span>
                  </div>
                  <Button
                    variant="outline"
                    disabled={
                      !workflow.data?.stages.some(
                        (s) => s.name === funnel.data!.labels[focus],
                      )
                    }
                    onClick={() => {
                      const stage = workflow.data?.stages.find(
                        (s) => s.name === funnel.data!.labels[focus],
                      );
                      if (stage)
                        navigate(
                          "/interactions?" +
                            new URLSearchParams({ group, stage: stage.code }),
                        );
                    }}
                  >
                    Открыть записи ↗
                  </Button>
                </div>
              )}
            </Panel>
            <Panel title="Направления работы">
              <p className="chart-hint">
                Доли взаимодействий по направлениям. Отменённые записи
                исключены.
              </p>
              <State query={distribution}>
                {distribution.data && (
                  <ChartView
                    chart={distribution.data}
                    initial={
                      distribution.data.values.filter((v) => v > 0).length <= 6
                        ? "donut"
                        : "bar"
                    }
                  />
                )}
              </State>
              <div className="dashboard-note">
                <strong>Как читать график</strong>
                <p>
                  Круговая диаграмма показывает состав портфеля. Для точного
                  сравнения близких значений переключитесь на столбцы.
                </p>
              </div>
            </Panel>
            <Panel title="Где процесс занимает больше времени">
              <p className="chart-hint">
                Средняя длительность завершённых посещений этапа, в днях.
                Незавершённые посещения не включены.
              </p>
              <State query={duration}>
                {duration.data && (
                  <ChartView chart={duration.data} initial="dot" duration />
                )}
              </State>
            </Panel>
          </div>
          <div className="dashboard-footnote">
            Срезы обновляются при изменении данных. PDF содержит серверный отчёт
            по выбранной группе; PNG сохраняет выбранный вид графика. Временные
            тренды доступны на вкладке «Динамика во времени».
          </div>
        </>
      )}
    </>
  );
}
export function RatingPage({ me }: { me: Me }) {
  const [entity, setEntity] = useState("program");
  const [order, setOrder] = useState("score");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [direction, setDirection] = useState("");
  const [dirty, setDirty] = useState(false);
  const [weights, setWeights] = useState([40, 40, 20]);
  const [applied, setApplied] = useState<number[] | null>(null);
  const dirs = useResource<Schema["DirectionRef"][]>("/directions");
  const q = useResource<Schema["RatingOut"]>("/analytics/rating", {
    entity,
    order,
    period_from: from || undefined,
    period_to: to || undefined,
    direction_id: direction || undefined,
    ...(applied
      ? {
          w_applications: applied[0],
          w_students: applied[1],
          w_streams: applied[2],
        }
      : {}),
  });
  useEffect(() => {
    if (q.data && !dirty && !applied)
      setWeights([
        q.data.weights.applications ?? 40,
        q.data.weights.students ?? 40,
        q.data.weights.streams ?? 20,
      ]);
  }, [q.data, dirty, applied]);
  const save = useAction(() =>
    api.send(
      "/analytics/rating/weights",
      {
        w_applications: weights[0],
        w_students: weights[1],
        w_streams: weights[2],
      },
      "PUT",
    ),
  );
  const sum = weights.reduce((a, b) => a + b, 0);
  return (
    <>
      <Heading
        eyebrow="АНАЛИТИКА"
        title="Рейтинг востребованности"
        text="Баллы, которые можно объяснить. Заявки, обучающиеся и потоки в одном сравнении."
      />
      <Panel title="Параметры рейтинга">
        <div className="form-grid">
          <Field label="Что сравниваем">
            <Select value={entity} onChange={(e) => setEntity(e.target.value)}>
              <option value="program">Программы</option>
              <option value="university">Вузы</option>
            </Select>
          </Field>
          <Field label="Порядок">
            <Select value={order} onChange={(e) => setOrder(e.target.value)}>
              <option value="score">По расчётному баллу</option>
              <option value="priority">По ручному приоритету</option>
            </Select>
          </Field>
          <Field label="Направление">
            <Select
              value={direction}
              onChange={(e) => setDirection(e.target.value)}
            >
              <option value="">Все направления</option>
              {dirs.data?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Начало периода">
            <input
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
            />
          </Field>
          <Field label="Конец периода">
            <input
              type="date"
              min={from}
              value={to}
              onChange={(e) => setTo(e.target.value)}
            />
          </Field>
        </div>
        <div className="weight-grid">
          {["Заявки", "Обучающиеся", "Потоки"].map((label, i) => (
            <Field key={label} label={`${label} · ${weights[i]}%`}>
              <input
                type="range"
                min="0"
                max="100"
                value={weights[i]}
                onChange={(e) => {
                  setDirty(true);
                  setWeights(
                    weights.map((v, j) =>
                      i === j ? Number(e.target.value) : v,
                    ),
                  );
                }}
              />
            </Field>
          ))}
        </div>
        <div className="service-toolbar">
          <span className={sum !== 100 ? "error-copy" : ""}>
            Сумма весов: {sum}% из 100%
          </span>
          <Button
            disabled={sum !== 100}
            onClick={() => setApplied([...weights])}
          >
            Пересчитать
          </Button>
          {me.role !== "kam" && (
            <Button
              variant="outline"
              disabled={sum !== 100 || save.isPending}
              onClick={() => save.mutate()}
            >
              Сохранить по умолчанию
            </Button>
          )}
        </div>
        <Failure error={save.error} />
        {save.isSuccess && <p role="status">Веса сохранены.</p>}
      </Panel>
      <Panel title="Результаты сравнения">
        <State query={q}>
          {order === "priority" && (
            <p>Строки упорядочены вручную. Место и балл остаются расчётными.</p>
          )}
          <div className="rating-list">
            {q.data?.rows.map((r) => (
              <article key={r.id} className="rating-row">
                <span className="rating-place">{r.place}</span>
                <div>
                  <h3>{r.name}</h3>
                  <small>
                    {r.direction_name} ·{" "}
                    {r.place_change === null
                      ? "Впервые в рейтинге"
                      : r.place_change > 0
                        ? `↑ ${r.place_change}`
                        : r.place_change < 0
                          ? `↓ ${-r.place_change}`
                          : "Без изменений"}
                  </small>
                  <div className="contribution-bar">
                    {r.contributions.map((c, i) => (
                      <span
                        key={c.metric}
                        style={{
                          width: `${c.contribution}%`,
                          background: ["#7700ff", "#ff4f12", "#a2c5ff"][i],
                        }}
                        title={`${names[c.metric] || c.metric}: ${c.contribution.toFixed(1)}`}
                      />
                    ))}
                  </div>
                  <div className="contribution-legend">
                    {r.contributions.map((c) => (
                      <small key={c.metric}>
                        {names[c.metric] || c.metric}:{" "}
                        {c.contribution.toFixed(1)}
                      </small>
                    ))}
                  </div>
                  {!r.complete && (
                    <p className="incomplete">
                      Неполные данные:{" "}
                      {r.missing_metrics.map((m) => names[m] || m).join(", ")}
                    </p>
                  )}
                </div>
                <strong className="rating-score">
                  {r.score.toFixed(1)}
                  <small>балла</small>
                </strong>
                {entity === "program" && me.role !== "kam" && (
                  <Priority row={r} />
                )}
              </article>
            ))}
            {q.data && !q.data.rows.length && <EmptyData />}
          </div>
        </State>
      </Panel>
    </>
  );
}
function Priority({ row }: { row: Schema["RatingRowOut"] }) {
  const [value, setValue] = useState(row.priority);
  const action = useAction(() =>
    api.send(`/programs/${row.id}/priority`, { priority: value }, "PUT"),
  );
  return (
    <form
      className="priority-field"
      onSubmit={(e) => {
        e.preventDefault();
        action.mutate();
      }}
    >
      <Field label="Приоритет">
        <input
          type="number"
          min="0"
          max="100"
          value={value}
          onChange={(e) => setValue(Number(e.target.value))}
        />
      </Field>
      <Button
        variant="ghost"
        disabled={action.isPending || value === row.priority}
      >
        Сохранить
      </Button>
      <Failure error={action.error} />
    </form>
  );
}
