import { Link, useNavigate } from "react-router-dom";
import type { Schema } from "../api/types";
import { Panel, State, useResource } from "./shared";
import { ChartView } from "./Charts";
export function RadarCharts({ group }: { group: string }) {
  const navigate = useNavigate();
  const groups = useResource<Schema["CounterpartyGroupOut"][]>(
    "/counterparty-groups",
  );
  const selected = groups.data?.find((g) => g.id === group);
  const workflow = useResource<Schema["WorkflowOut"]>(
    selected
      ? `/workflows/${selected.workflow_template_id}`
      : "/workflows/default",
  );
  const directions = useResource<Schema["DirectionRef"][]>("/directions");
  const funnel = useResource<Schema["ChartOut"]>("/analytics/stats/funnel", {
    group_id: group || undefined,
  });
  const distribution = useResource<Schema["ChartOut"]>(
    "/analytics/stats/distribution",
    { group_id: group || undefined },
  );
  function pick(which: number, index: number) {
    const params = new URLSearchParams();
    if (group) params.set("group", group);
    if (which === 0) {
      const label = funnel.data?.labels[index];
      const stage = workflow.data?.stages.find((s) => s.name === label);
      if (!stage) return;
      const chartGroup =
        group ||
        groups.data?.find(
          (g) => g.workflow_template_id === workflow.data?.template_id,
        )?.id;
      if (chartGroup) params.set("group", chartGroup);
      params.set("stage", stage.code);
    } else {
      const dir = directions.data?.find(
        (d) => d.name === distribution.data?.labels[index],
      );
      if (!dir) return;
      params.set("direction", dir.id);
    }
    navigate("/interactions?" + params);
  }
  return (
    <div className="analytics-grid radar-charts">
      {[funnel, distribution].map((q, i) => (
        <Panel
          key={i}
          title={
            q.data?.title || (i ? "Направления работы" : "Движение по этапам")
          }
          action={
            <Link className="text-link" to="/analytics/stats">
              Подробнее ↗
            </Link>
          }
        >
          <p className="chart-hint">
            Нажмите на этап или направление, чтобы открыть записи
          </p>
          <State query={q}>
            {q.data && (
              <ChartView
                initial={
                  i === 1 && q.data.values.filter((v) => v > 0).length <= 6
                    ? "donut"
                    : "bar"
                }
                chart={q.data}
                onPick={
                  i === 0
                    ? workflow.data
                      ? (n) => pick(i, n)
                      : undefined
                    : directions.data
                      ? (n) => pick(i, n)
                      : undefined
                }
              />
            )}
          </State>
        </Panel>
      ))}
    </div>
  );
}
