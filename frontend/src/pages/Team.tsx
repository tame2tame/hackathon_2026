import { useState } from "react";
import { Link } from "react-router-dom";
import { Heading } from "../App";
import { api } from "../api/runtime";
import type { Schema } from "../api/types";
import { kinds, roleNames } from "../lib/data";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
import {
  Failure,
  Field,
  Panel,
  State,
  useAction,
  useResource,
  Pager,
} from "./shared";
export function TeamPage() {
  const users = useResource<Schema["UserOut"][]>("/users");
  const summary = useResource<Schema["SignalSummaryOut"]>("/signals/summary");
  const [owner, setOwner] = useState("");
  const [next, setNext] = useState("");
  const [reason, setReason] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const rows = useResource<Schema["Page_InteractionListItem_"]>(
    "/interactions",
    { owner_id: owner || undefined, page, page_size: 20 },
  );
  const action = useAction(() =>
    api.send<Schema["BulkResult"]>("/interactions/bulk-owner", {
      interaction_ids: selected,
      owner_id: next,
      reason,
    }),
  );
  return (
    <>
      <Heading
        eyebrow="УПРАВЛЕНИЕ"
        title="Команда"
        text="Нагрузка, сигналы и распределение ответственности."
      />
      <Panel title="Сигналы команды">
        <State query={summary}>
          <div className="table-scroll">
            <table className="service-table heatmap">
              <thead>
                <tr>
                  <th>Сотрудник</th>
                  {summary.data?.kinds.map((k) => (
                    <th key={k}>{kinds[k]}</th>
                  ))}
                  <th>Всего</th>
                </tr>
              </thead>
              <tbody>
                {summary.data?.rows.map((r) => (
                  <tr key={r.owner.id}>
                    <td>
                      <button
                        onClick={() => {
                          setOwner(r.owner.id);
                          setPage(1);
                          setSelected([]);
                        }}
                      >
                        {r.owner.full_name}
                      </button>
                    </td>
                    {summary.data?.kinds.map((k) => (
                      <td key={k}>
                        <span
                          style={{
                            background: `rgba(119,0,255,${Math.min(0.6, (r.counts[k] || 0) / 20)})`,
                          }}
                        >
                          {r.counts[k] || 0}
                        </span>
                      </td>
                    ))}
                    <td>{r.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </State>
      </Panel>
      <Panel title="Передать взаимодействия">
        <div className="form-grid">
          <Field label="Текущий ответственный">
            <Select
              value={owner}
              onChange={(e) => {
                setOwner(e.target.value);
                setPage(1);
                setSelected([]);
              }}
            >
              <option value="">Все сотрудники</option>
              {users.data?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name} · {roleNames[u.role]}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Новый ответственный">
            <Select value={next} onChange={(e) => setNext(e.target.value)}>
              <option value="">Выберите сотрудника</option>
              {users.data?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Причина передачи">
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Например, перераспределение нагрузки"
            />
          </Field>
        </div>
        <State query={rows}>
          {rows.data?.items.map((r) => (
            <label className="service-row" key={r.id}>
              <input
                type="checkbox"
                checked={selected.includes(r.id)}
                onChange={(e) =>
                  setSelected(
                    e.target.checked
                      ? [...selected, r.id]
                      : selected.filter((id) => id !== r.id),
                  )
                }
              />
              <span className="grow">
                <strong>{r.counterparty.name}</strong>
                <small>
                  {r.program.name} · {r.owner.full_name}
                </small>
              </span>
              <Link to={`/interactions/${r.id}`}>Открыть ↗</Link>
            </label>
          ))}
          <Pager page={page} total={rows.data?.total || 0} onPage={setPage} />
        </State>
        <Failure error={action.error} />
        <Button
          disabled={
            !selected.length || !next || !reason.trim() || action.isPending
          }
          onClick={() => action.mutate()}
        >
          Передать выбранные ({selected.length})
        </Button>
        {action.data && (
          <div className="bulk-results" role="status">
            {action.data.results.map((r) => (
              <p key={r.interaction_id}>
                {rows.data?.items.find((i) => i.id === r.interaction_id)
                  ?.counterparty.name || r.interaction_id}
                : {r.ok ? "Передано" : r.detail || r.code}
              </p>
            ))}
          </div>
        )}
      </Panel>
    </>
  );
}
