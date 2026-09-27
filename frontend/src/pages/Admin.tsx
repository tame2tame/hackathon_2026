import { CreateTeam } from "./Groups";
import { Channels } from "./Channels";
import { useState } from "react";
import { Heading } from "../App";
import { api } from "../api/runtime";
import type { Schema } from "../api/types";
import { roleNames } from "../lib/data";
import { Button } from "../components/ui/button";
import { Select } from "../components/ui/select";
import {
  Failure,
  Field,
  Panel,
  State,
  enc,
  when,
  useAction,
  useResource,
} from "./shared";
export function SettingsPage() {
  const q = useResource<Schema["SettingOut"][]>("/admin/settings");
  return (
    <>
      <Heading
        eyebrow="АДМИНИСТРИРОВАНИЕ"
        title="Настройки"
        text="Пороги радара и правила эскалации применяются ко всем активным записям."
      />
      <State query={q}>
        {q.data?.map((s) => (
          <Setting key={s.key} setting={s} />
        ))}
      </State>
      <Channels />
    </>
  );
}
const settingLabels: Record<string, string> = {
  license_warn_days: "Предупредить о лицензии, дней",
  license_critical_days: "Критический срок лицензии, дней",
  inactivity_low_days: "Предупредить о простое, дней",
  inactivity_medium_days: "Критический простой, дней",
  days: "Дней без изменений",
  enabled: "Включено",
  notify_role: "Кому сообщить",
  w_applications: "Вес заявок",
  w_students: "Вес обучающихся",
  w_streams: "Вес потоков",
};
function Setting({ setting: s }: { setting: Schema["SettingOut"] }) {
  const [value, setValue] = useState(s.value);
  const save = useAction(() =>
    api.send(`/admin/settings/${enc(s.key)}`, { value }, "PUT"),
  );
  return (
    <Panel title={s.description}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <div className="form-grid">
          {Object.entries(value).map(([k, v]) => (
            <Field key={k} label={settingLabels[k] || k}>
              {k === "notify_role" ? (
                <Select
                  value={String(v)}
                  onChange={(e) => setValue({ ...value, [k]: e.target.value })}
                >
                  <option value="manager">Руководитель</option>
                  <option value="admin">Администратор</option>
                </Select>
              ) : typeof v === "boolean" ? (
                <input
                  type="checkbox"
                  checked={v}
                  onChange={(e) =>
                    setValue({ ...value, [k]: e.target.checked })
                  }
                />
              ) : (
                <input
                  type={typeof v === "number" ? "number" : "text"}
                  min="0"
                  required
                  value={String(v)}
                  onChange={(e) =>
                    setValue({
                      ...value,
                      [k]:
                        typeof v === "number"
                          ? Number(e.target.value)
                          : e.target.value,
                    })
                  }
                />
              )}
            </Field>
          ))}
        </div>
        <Failure error={save.error} />
        <Button disabled={save.isPending}>Сохранить</Button>
        {save.isSuccess && <p role="status">Настройка применена.</p>}
      </form>
    </Panel>
  );
}
export function AuditPage() {
  const [action, setAction] = useState("");
  const [kind, setKind] = useState("");
  const [limit, setLimit] = useState(100);
  const q = useResource<Schema["AuditEntryOut"][]>("/admin/audit", {
    action: action || undefined,
    entity_kind: kind || undefined,
    limit,
  });
  return (
    <>
      <Heading
        eyebrow="АДМИНИСТРИРОВАНИЕ"
        title="Журнал аудита"
        text="История изменений и просмотра данных. Записи журнала нельзя изменить."
      />
      <Panel title="События">
        <div className="form-grid">
          <Field label="Действие">
            <input
              value={action}
              placeholder="Например, interaction.transition"
              onChange={(e) => setAction(e.target.value)}
            />
          </Field>
          <Field label="Объект">
            <input
              value={kind}
              placeholder="Например, interaction"
              onChange={(e) => setKind(e.target.value)}
            />
          </Field>
          <Field label="Показать событий">
            <Select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            >
              {[50, 100, 250, 500].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <State query={q}>
          {q.data?.map((r) => (
            <details className="audit-entry" key={r.id}>
              <summary>
                <span>{when(r.occurred_at)}</span>
                <strong>{r.action}</strong>
                <small>{r.entity_kind}</small>
              </summary>
              <p>
                Автор: {r.actor_user_id || "Система"} · Код запроса:{" "}
                {r.trace_id || "—"}
              </p>
              <div className="form-grid">
                <div>
                  <h3>До</h3>
                  <pre>{JSON.stringify(r.before, null, 2)}</pre>
                </div>
                <div>
                  <h3>После</h3>
                  <pre>{JSON.stringify(r.after, null, 2)}</pre>
                </div>
              </div>
            </details>
          ))}
        </State>
      </Panel>
    </>
  );
}
export function AccessPage() {
  const users = useResource<Schema["AdminUserOut"][]>("/admin/users");
  const teams = useResource<Schema["TeamOut"][]>("/admin/teams");
  const rules = useResource<Schema["AccessRuleOut"][]>("/admin/access-rules");
  const [subject, setSubject] = useState("");
  const [scope, setScope] = useState("group");
  const [scopeId, setScopeId] = useState("");
  const [effect, setEffect] = useState("deny");
  const [comment, setComment] = useState("");
  const options = useResource<
    | Schema["CounterpartyGroupOut"][]
    | Schema["DirectionRef"][]
    | Schema["ProgramRef"][]
    | Schema["Page_UniversityOut_"]
  >(
    scope === "group"
      ? "/counterparty-groups"
      : scope === "university"
        ? "/universities"
        : scope === "direction"
          ? "/directions"
          : "/programs",
  );
  const opts = options.data
    ? Array.isArray(options.data)
      ? options.data
      : options.data.items
    : [];
  const add = useAction(() =>
    api.send("/admin/access-rules", {
      subject_user_id: subject,
      scope_kind: scope,
      scope_id: scopeId,
      effect,
      comment,
    }),
  );
  const remove = useAction((id: string) =>
    api.request(`/api/v1/admin/access-rules/${id}`, { method: "DELETE" }),
  );
  return (
    <>
      <Heading
        eyebrow="АДМИНИСТРИРОВАНИЕ"
        title="Пользователи и доступ"
        text="Роли, команды и точечные правила видимости."
      />
      <Panel title="Сотрудники">
        <State query={users}>
          {users.data?.map((u) => (
            <UserEditor key={u.id} user={u} teams={teams.data || []} />
          ))}
        </State>
      </Panel>
      <CreateTeam />
      <Panel title="Правила доступа">
        <p>Запрет имеет приоритет над разрешением.</p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            add.mutate();
          }}
        >
          <div className="form-grid">
            <Field label="Сотрудник">
              <Select
                required
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              >
                <option value="">Выберите сотрудника</option>
                {users.data?.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Область">
              <Select
                value={scope}
                onChange={(e) => {
                  setScope(e.target.value);
                  setScopeId("");
                }}
              >
                {Object.entries({
                  group: "Группа",
                  university: "Вуз",
                  direction: "Направление",
                  program: "Программа",
                }).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Объект">
              <Select
                value={scopeId}
                onChange={(e) => setScopeId(e.target.value)}
              >
                <option value="">Выберите объект</option>
                {opts.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Действие">
              <Select
                value={effect}
                onChange={(e) => setEffect(e.target.value)}
              >
                <option value="deny">Запретить</option>
                <option value="allow">Разрешить</option>
              </Select>
            </Field>
            <Field label="Обоснование">
              <input
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
            </Field>
          </div>
          <Button disabled={!subject || !scopeId || add.isPending}>
            Добавить правило
          </Button>
          <Failure error={add.error || remove.error} />
        </form>
        <State query={rules}>
          {rules.data?.map((r) => (
            <div className="service-row" key={r.id}>
              <div className="grow">
                <strong>
                  {users.data?.find((u) => u.id === r.subject_user_id)
                    ?.full_name || r.subject_role}
                </strong>
                <p>
                  {r.effect === "deny" ? "Запрет" : "Разрешение"} ·{" "}
                  {r.scope_kind} · {r.comment}
                </p>
              </div>
              <Button
                variant="outline"
                disabled={remove.isPending}
                onClick={() => remove.mutate(r.id)}
              >
                Убрать правило
              </Button>
            </div>
          ))}
        </State>
      </Panel>
    </>
  );
}
function UserEditor({
  user: u,
  teams,
}: {
  user: Schema["AdminUserOut"];
  teams: Schema["TeamOut"][];
}) {
  const [role, setRole] = useState(u.role);
  const [team, setTeam] = useState(u.team_id || "");
  const [active, setActive] = useState(u.is_active);
  const save = useAction(() =>
    api.send(
      `/admin/users/${u.id}`,
      { role, team_id: team || null, is_active: active },
      "PATCH",
    ),
  );
  return (
    <form
      className="service-row"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      <div className="grow">
        <h3>{u.full_name}</h3>
        <small>{u.email}</small>
      </div>
      <Select
        aria-label={`Роль ${u.full_name}`}
        value={role}
        onChange={(e) => setRole(e.target.value as Schema["Role"])}
      >
        {Object.entries(roleNames).map(([k, v]) => (
          <option key={k} value={k}>
            {v}
          </option>
        ))}
      </Select>
      <Select
        aria-label={`Команда ${u.full_name}`}
        value={team}
        onChange={(e) => setTeam(e.target.value)}
      >
        <option value="">Без команды</option>
        {teams.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </Select>
      <label>
        <input
          type="checkbox"
          checked={active}
          onChange={(e) => setActive(e.target.checked)}
        />{" "}
        Активен
      </label>
      <Button variant="outline" disabled={save.isPending}>
        Сохранить
      </Button>
      <Failure error={save.error} />
    </form>
  );
}
