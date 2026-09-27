import { useState } from "react";
import { api } from "../api/runtime";
import type { Schema } from "../api/types";
import { Button } from "../components/ui/button";
import {
  Field,
  Panel,
  State,
  Failure,
  useAction,
  useResource,
  when,
} from "./shared";
export function Channels() {
  const q = useResource<Schema["ChannelOut"][]>("/admin/notification-channels");
  const deliveries = useResource<Schema["DeliveryOut"][]>(
    "/admin/notification-deliveries",
  );
  const escalation = useAction(() =>
    api.send<Schema["EscalationRunOut"]>("/admin/escalations/run"),
  );
  return (
    <>
      <Panel title="Каналы уведомлений">
        <State query={q}>
          {q.data?.map((c) => (
            <Channel key={c.kind} item={c} />
          ))}
        </State>
      </Panel>
      <Panel
        title="Доставка уведомлений"
        action={
          <Button
            variant="outline"
            disabled={escalation.isPending}
            onClick={() => escalation.mutate()}
          >
            Проверить зависшие записи
          </Button>
        }
      >
        <Failure error={escalation.error} />
        <State query={deliveries}>
          {deliveries.data?.map((d) => (
            <div className="service-row" key={d.id}>
              <span>{d.channel_kind}</span>
              <span>{d.status}</span>
              <small>
                Попыток: {d.attempts} · Следующая: {when(d.next_attempt_at)}
              </small>
            </div>
          ))}
        </State>
      </Panel>
    </>
  );
}
function Channel({ item: c }: { item: Schema["ChannelOut"] }) {
  const [enabled, setEnabled] = useState(c.is_enabled);
  const [mock, setMock] = useState(c.is_mock);
  const [secret, setSecret] = useState(c.secret_ref || "");
  const [settings, setSettings] = useState(c.settings);
  const save = useAction(() =>
    api.send(
      `/admin/notification-channels/${c.kind}`,
      {
        is_enabled: enabled,
        is_mock: mock,
        secret_ref: secret || null,
        settings,
      },
      "PUT",
    ),
  );
  return (
    <form
      className="channel-card"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      <h3>{c.name}</h3>
      <div className="column-picker">
        <label>
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
          />{" "}
          Доставка включена
        </label>
        <label>
          <input
            type="checkbox"
            checked={mock}
            onChange={(e) => setMock(e.target.checked)}
          />{" "}
          Тестовый канал
        </label>
      </div>
      <div className="form-grid">
        {Object.entries(settings).map(([k, v]) => (
          <Field key={k} label={k}>
            <input
              value={String(v)}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  [k]:
                    typeof v === "number"
                      ? Number(e.target.value)
                      : e.target.value,
                })
              }
            />
          </Field>
        ))}
        <Field label="Имя переменной с секретом">
          <input
            placeholder="NOTIFY_…"
            pattern="NOTIFY_[A-Z0-9_]+"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
          />
        </Field>
      </div>
      <small>
        {c.secret_configured ? "Секрет задан на сервере" : "Секрет не настроен"}
      </small>
      <div>
        <Button variant="outline" disabled={save.isPending}>
          Сохранить канал
        </Button>
      </div>
      <Failure error={save.error} />
    </form>
  );
}
