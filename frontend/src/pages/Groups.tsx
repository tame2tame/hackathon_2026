import { useState } from "react";
import { api } from "../api/runtime";
import type { Me, Schema } from "../api/types";
import { Button } from "../components/ui/button";
import { Select } from "../components/ui/select";
import { Failure, Field, Panel, State, useAction, useResource } from "./shared";
export function Groups({ me }: { me: Me }) {
  const q = useResource<Schema["CounterpartyGroupOut"][]>(
    "/counterparty-groups",
  );
  const workflows = useResource<Schema["WorkflowSummaryOut"][]>("/workflows");
  const [form, setForm] = useState<Schema["CounterpartyGroupCreate"]>({
    name: "",
    code: "",
    workflow_template_id: "",
    position: 0,
  });
  const add = useAction(() => api.send("/admin/counterparty-groups", form));
  return (
    <>
      <Panel title="Группы контрагентов">
        <State query={q}>
          {q.data?.map((g) => (
            <Group
              key={g.id}
              group={g}
              me={me}
              workflows={workflows.data || []}
            />
          ))}
        </State>
      </Panel>
      {me.role === "admin" && (
        <Panel title="Новая группа">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              add.mutate();
            }}
          >
            <div className="form-grid">
              <Field label="Название">
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </Field>
              <Field label="Код группы">
                <input
                  required
                  pattern="[a-z0-9_-]+"
                  placeholder="Например, partners"
                  value={form.code}
                  onChange={(e) => setForm({ ...form, code: e.target.value })}
                />
              </Field>
              <Field label="Процесс">
                <Select
                  value={form.workflow_template_id}
                  onChange={(e) =>
                    setForm({ ...form, workflow_template_id: e.target.value })
                  }
                >
                  <option value="">Выберите процесс</option>
                  {workflows.data
                    ?.filter((w) => w.published_version_id)
                    .map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.name}
                      </option>
                    ))}
                </Select>
              </Field>
            </div>
            <Button disabled={!form.workflow_template_id || add.isPending}>
              Создать группу
            </Button>
            <Failure error={add.error} />
          </form>
        </Panel>
      )}
    </>
  );
}
function Group({
  group: g,
  me,
  workflows,
}: {
  group: Schema["CounterpartyGroupOut"];
  me: Me;
  workflows: Schema["WorkflowSummaryOut"][];
}) {
  const [name, setName] = useState(g.name);
  const [process, setProcess] = useState(g.workflow_template_id);
  const save = useAction(() =>
    api.send(
      `/admin/counterparty-groups/${g.id}`,
      { name, workflow_template_id: process },
      "PATCH",
    ),
  );
  const archive = useAction(() =>
    api.send(`/admin/counterparty-groups/${g.id}/archive`),
  );
  return (
    <form
      className="service-row"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      <Field label="Название группы">
        <input
          value={name}
          disabled={me.role !== "admin"}
          onChange={(e) => setName(e.target.value)}
        />
      </Field>
      <Field label="Процесс">
        <Select
          disabled={me.role !== "admin"}
          value={process}
          onChange={(e) => setProcess(e.target.value)}
        >
          {workflows
            .filter((w) => w.published_version_id)
            .map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
        </Select>
      </Field>
      {me.role === "admin" && (
        <>
          <Button variant="outline" disabled={save.isPending}>
            Сохранить
          </Button>
          <Button
            type="button"
            variant="ghost"
            disabled={archive.isPending}
            onClick={() => archive.mutate()}
          >
            В архив
          </Button>
        </>
      )}
      <Failure error={save.error || archive.error} />
    </form>
  );
}
export function CreateProcess() {
  const [name, setName] = useState("");
  const create = useAction(() => api.send("/workflows", { name }));
  return (
    <details className="bulk-tools">
      <summary>Создать новый процесс</summary>
      <form
        className="service-toolbar"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <Field label="Название процесса">
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </Field>
        <Button disabled={!name.trim() || create.isPending}>Создать</Button>
      </form>
      <Failure error={create.error} />
    </details>
  );
}
export function CreateTeam() {
  const [name, setName] = useState("");
  const [manager, setManager] = useState("");
  const users = useResource<Schema["AdminUserOut"][]>("/admin/users");
  const create = useAction(() =>
    api.send("/admin/teams", { name, manager_user_id: manager || null }),
  );
  return (
    <Panel title="Новая команда">
      <form
        className="service-toolbar"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <Field label="Название">
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </Field>
        <Field label="Руководитель">
          <Select value={manager} onChange={(e) => setManager(e.target.value)}>
            <option value="">Не назначен</option>
            {users.data
              ?.filter((u) => u.role === "manager" || u.role === "admin")
              .map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name}
                </option>
              ))}
          </Select>
        </Field>
        <Button disabled={!name.trim() || create.isPending}>
          Создать команду
        </Button>
      </form>
      <Failure error={create.error} />
    </Panel>
  );
}
