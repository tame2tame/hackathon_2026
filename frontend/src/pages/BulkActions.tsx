import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/runtime";
import type { Schema } from "../api/types";
import { Button } from "../components/ui/button";
import { Select } from "../components/ui/select";
import { Failure, Field, useAction } from "./shared";
export function BulkActions({
  items,
  workflow,
}: {
  items: Schema["InteractionListItem"][];
  workflow?: Schema["WorkflowOut"];
}) {
  const [ids, setIds] = useState<string[]>([]);
  const [target, setTarget] = useState("");
  const [comment, setComment] = useState("");
  const eligible = items.filter(
    (r) =>
      r.status === "active" &&
      workflow?.stages.some((s) => s.code === r.stage.code && s.bulk_allowed),
  );
  const action = useAction(() =>
    api.send<Schema["BulkResult"]>("/interactions/bulk-transitions", {
      interaction_ids: ids.filter((id) => eligible.some((r) => r.id === id)),
      to_stage_code: target,
      comment,
    }),
  );
  if (!workflow) return null;
  return (
    <details className="bulk-tools">
      <summary>Групповой переход</summary>
      <p>
        Выберите записи на этой странице. Переходы с обязательным документом
        выполняются из карточки.
      </p>
      {eligible.map((r) => (
        <label className="service-row" key={r.id}>
          <input
            type="checkbox"
            checked={ids.includes(r.id)}
            onChange={(e) =>
              setIds(
                e.target.checked
                  ? [...ids, r.id]
                  : ids.filter((id) => id !== r.id),
              )
            }
          />
          <span>
            {r.counterparty.name} · {r.program.name}
          </span>
        </label>
      ))}
      {!eligible.length && (
        <p>На этой странице нет записей, доступных для группового перехода.</p>
      )}
      <div className="form-grid">
        <Field label="Новый этап">
          <Select value={target} onChange={(e) => setTarget(e.target.value)}>
            <option value="">Выберите этап</option>
            {workflow.stages.map((s) => (
              <option key={s.id} value={s.code}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Комментарий">
          <input value={comment} onChange={(e) => setComment(e.target.value)} />
        </Field>
      </div>
      <Button
        disabled={
          !target ||
          !comment.trim() ||
          !ids.some((id) => eligible.some((r) => r.id === id)) ||
          action.isPending
        }
        onClick={() => action.mutate()}
      >
        Перевести выбранные
      </Button>
      <Failure error={action.error} />
      {action.data?.results.map((r) => (
        <p key={r.interaction_id}>
          <Link to={`/interactions/${r.interaction_id}`}>
            {items.find((i) => i.id === r.interaction_id)?.counterparty.name ||
              "Запись"}
          </Link>
          : {r.ok ? "Этап изменён" : r.detail || r.code}
        </p>
      ))}
    </details>
  );
}
export function Kanban({ items }: { items: Schema["InteractionListItem"][] }) {
  const stages = [
    ...new Map(items.map((i) => [i.stage.code, i.stage])).values(),
  ].sort((a, b) => a.position - b.position);
  return (
    <div className="kanban-board">
      {stages.map((s) => (
        <section key={s.code} className="kanban-column">
          <h3>
            {s.name}
            <span className="count-pill">
              {items.filter((i) => i.stage.code === s.code).length}
            </span>
          </h3>
          {items
            .filter((i) => i.stage.code === s.code)
            .map((i) => (
              <Link
                key={i.id}
                className="kanban-card"
                to={`/interactions/${i.id}`}
              >
                <strong>{i.counterparty.short_name}</strong>
                <p>{i.program.name}</p>
                <small>
                  {i.owner.full_name} · {i.days_on_stage} дн.
                </small>
                {i.open_signals.length > 0 && (
                  <span className="incomplete">
                    Сигналов: {i.open_signals.length}
                  </span>
                )}
              </Link>
            ))}
        </section>
      ))}
    </div>
  );
}
