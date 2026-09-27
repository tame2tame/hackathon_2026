import { useState } from "react";
import { Heading } from "../App";
import { api } from "../api/runtime";
import type { Me, Schema } from "../api/types";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
import {
  EmptyData,
  Failure,
  Field,
  Panel,
  State,
  Summary,
  names,
  when,
  useAction,
  useResource,
} from "./shared";
export function IntegrationsPage({ me }: { me: Me }) {
  const q = useResource<Schema["IntegrationSourceOut"][]>("/integrations");
  const apps = useResource<Schema["SiteApplicationOut"][]>(
    "/site-applications",
    { match_status: "unmatched" },
  );
  return (
    <>
      <Heading
        eyebrow="УПРАВЛЕНИЕ"
        title="Интеграции"
        text="Обмен с LMS и сайтом, состояние очередей и заявки, которым нужна помощь."
      />
      <State query={q}>
        {q.data?.map((s) => (
          <Source key={s.id} source={s} me={me} />
        ))}
      </State>
      <Panel title="Несопоставленные заявки">
        <State query={apps}>
          {apps.data?.map((a) => (
            <Match key={a.id} item={a} />
          ))}
          {!apps.data?.length && <EmptyData />}
        </State>
      </Panel>
    </>
  );
}
function Source({
  source: s,
  me,
}: {
  source: Schema["IntegrationSourceOut"];
  me: Me;
}) {
  const [expanded, setExpanded] = useState(false);
  const [status, setStatus] = useState("");
  const runs = useResource<Schema["SyncRunOut"][]>(
    `/integrations/${s.id}/runs`,
    {},
    expanded,
  );
  const outbox = useResource<Schema["OutboxEntryOut"][]>(
    `/integrations/${s.id}/outbox`,
    { status: status || undefined },
    expanded,
  );
  const run = useAction((direction: string) =>
    api.send<Schema["SyncRunOut"]>(`/integrations/${s.id}/${direction}`),
  );
  const toggle = useAction(() =>
    api.send(
      `/integrations/${s.id}`,
      { push_enabled: !s.push_enabled },
      "PATCH",
    ),
  );
  return (
    <Panel
      title={s.name}
      action={
        <span className="count-pill">
          {s.is_mock ? "Тестовый источник" : s.kind.toUpperCase()}
        </span>
      }
    >
      <p>{s.base_url}</p>
      <div className="summary-chips">
        <span>Получено: {when(s.last_sync_at)}</span>
        <span>Отправлено: {when(s.last_push_at)}</span>
        <span>Расписание: {s.schedule_cron || "Вручную"}</span>
      </div>
      <div className="service-toolbar">
        <Button disabled={run.isPending} onClick={() => run.mutate("sync")}>
          Получить данные
        </Button>
        <Button
          variant="outline"
          disabled={run.isPending || !s.push_enabled}
          onClick={() => run.mutate("push")}
        >
          Отправить очередь
        </Button>
        {me.role === "admin" && (
          <Button
            variant="outline"
            disabled={toggle.isPending}
            onClick={() => toggle.mutate()}
          >
            {s.push_enabled ? "Выключить отправку" : "Включить отправку"}
          </Button>
        )}
        <Button variant="ghost" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Скрыть журнал" : "Журнал и очередь"}
        </Button>
      </div>
      <Failure error={run.error || toggle.error} />
      {run.data && (
        <div role="status">
          <p>
            {names[run.data.status] || run.data.status}
            {run.data.error_code && ` · ${run.data.error_code}`}
          </p>
          <Summary stats={run.data.stats} />
        </div>
      )}
      {expanded && (
        <>
          <h3>Последние запуски</h3>
          <State query={runs}>
            {runs.data?.map((r) => (
              <div className="service-row" key={r.id}>
                <span>{when(r.started_at)}</span>
                <span>{r.direction === "pull" ? "Получение" : "Отправка"}</span>
                <strong>{names[r.status] || r.status}</strong>
                <small>{r.error_code}</small>
              </div>
            ))}
          </State>
          <Field label="Очередь отправки">
            <Select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Все состояния</option>
              {["pending", "sent", "failed"].map((k) => (
                <option key={k} value={k}>
                  {names[k]}
                </option>
              ))}
            </Select>
          </Field>
          <State query={outbox}>
            {outbox.data?.map((r) => (
              <div className="service-row" key={r.id}>
                <span>{names[r.status] || r.status}</span>
                <span>{r.reason}</span>
                <small>
                  Попыток: {r.attempts} · {r.last_error || "Ошибок нет"}
                </small>
              </div>
            ))}
            {!outbox.data?.length && <EmptyData />}
          </State>
        </>
      )}
    </Panel>
  );
}
function Match({ item }: { item: Schema["SiteApplicationOut"] }) {
  const [search, setSearch] = useState("");
  const [id, setId] = useState("");
  const rows = useResource<Schema["Page_InteractionListItem_"]>(
    "/interactions",
    { search, page_size: 20 },
  );
  const action = useAction(() =>
    api.send(`/site-applications/${item.id}/match`, { interaction_id: id }),
  );
  return (
    <div className="service-row">
      <div className="grow">
        <h3>{item.university_name}</h3>
        <p>
          {item.program_name} · {when(item.received_at)}
        </p>
        <input
          aria-label="Поиск взаимодействия"
          placeholder="Найти взаимодействие"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <Select
        aria-label="Взаимодействие для заявки"
        value={id}
        onChange={(e) => setId(e.target.value)}
      >
        <option value="">Выберите запись</option>
        {rows.data?.items.map((r) => (
          <option key={r.id} value={r.id}>
            {r.counterparty.name} · {r.program.name}
          </option>
        ))}
      </Select>
      <Button
        disabled={!id || action.isPending}
        onClick={() => action.mutate()}
      >
        Привязать
      </Button>
      <Failure error={action.error} />
    </div>
  );
}
