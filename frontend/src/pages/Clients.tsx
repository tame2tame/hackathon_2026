import { useState } from "react";
import { Heading } from "../App";
import { api } from "../api/runtime";
import { Payments } from "./Payments";
import type { Me, Schema } from "../api/types";
import { Button } from "../components/ui/button";
import { Select } from "../components/ui/select";
import {
  EmptyData,
  Failure,
  Field,
  Panel,
  State,
  Pager,
  useAction,
  useResource,
} from "./shared";
export function ClientsPage({ me }: { me: Me }) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState<Schema["ClientCreate"]>({
    kind: "person",
    name: "",
  });
  const q = useResource<Schema["Page_ClientListItem_"]>("/clients", {
    page,
    page_size: 20,
    search: search || undefined,
  });
  const add = useAction(async () => {
    const r = await api.send("/clients", form);
    setForm({ kind: "person", name: "" });
    return r;
  });
  return (
    <>
      <Heading
        eyebrow="РАБОЧЕЕ ПРОСТРАНСТВО"
        title="Клиенты"
        text="Физические лица и организации, которые обучаются в ИТ Школе."
      />
      <Payments me={me} />
      <Panel title="Клиенты">
        <Field label="Поиск по имени или организации">
          <input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </Field>
        <State query={q}>
          {q.data?.items.map((c) => (
            <Client key={c.id} item={c} />
          ))}
          {!q.data?.items.length && <EmptyData />}
          <Pager page={page} total={q.data?.total || 0} onPage={setPage} />
        </State>
      </Panel>
      <Panel title="Новый клиент">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            add.mutate();
          }}
        >
          <div className="form-grid">
            <Field label="Тип">
              <Select
                value={form.kind}
                onChange={(e) =>
                  setForm({
                    ...form,
                    kind: e.target.value as "person" | "organization",
                  })
                }
              >
                <option value="person">Физическое лицо</option>
                <option value="organization">Организация</option>
              </Select>
            </Field>
            <Field label="Имя или название">
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </Field>
            {form.kind === "organization" && (
              <Field label="ИНН">
                <input
                  pattern="[0-9]{10}|[0-9]{12}"
                  value={form.inn || ""}
                  onChange={(e) =>
                    setForm({ ...form, inn: e.target.value || null })
                  }
                />
              </Field>
            )}
            {(["city", "email", "phone"] as const).map((k) => (
              <Field
                key={k}
                label={{ city: "Город", email: "Email", phone: "Телефон" }[k]}
              >
                <input
                  type={
                    k === "email" ? "email" : k === "phone" ? "tel" : "text"
                  }
                  value={form[k] || ""}
                  onChange={(e) =>
                    setForm({ ...form, [k]: e.target.value || null })
                  }
                />
              </Field>
            ))}
          </div>
          <Button disabled={!form.name.trim() || add.isPending}>
            Добавить клиента
          </Button>
          <Failure error={add.error} />
        </form>
      </Panel>
    </>
  );
}
function Client({ item: c }: { item: Schema["ClientListItem"] }) {
  const [open, setOpen] = useState(false);
  const q = useResource<Schema["ClientOut"]>(`/clients/${c.id}`, {}, open);
  return (
    <div className="service-row">
      <div className="grow">
        <h3>{c.name}</h3>
        <small>
          {c.kind === "person" ? "Физическое лицо" : "Организация"} ·{" "}
          {c.city || "Город не указан"}
        </small>
        {open && (
          <State query={q}>
            <p>
              {q.data?.email || "Email не указан"} ·{" "}
              {q.data?.phone || "Телефон не указан"}
            </p>
          </State>
        )}
      </div>
      <Button variant="outline" onClick={() => setOpen(!open)}>
        {open ? "Скрыть контакты" : "Показать контакты"}
      </Button>
    </div>
  );
}
export function Contacts({ id }: { id: string }) {
  const q = useResource<Schema["ContactOut"][]>(`/universities/${id}/contacts`);
  const [form, setForm] = useState<Schema["ContactCreate"]>({ full_name: "" });
  const create = useAction(async () => {
    const r = await api.send(`/universities/${id}/contacts`, form);
    setForm({ full_name: "" });
    return r;
  });
  const archive = useAction((contactId: string) =>
    api.send(`/contacts/${contactId}/archive`),
  );
  return (
    <Panel title="Контактные лица">
      <State query={q}>
        {q.data?.map((c) => (
          <div className="service-row" key={c.id}>
            <div className="grow">
              <h3>{c.full_name}</h3>
              <small>
                {c.position} · {c.email || "Нет email"} ·{" "}
                {c.phone || "Нет телефона"}
              </small>
            </div>
            <Button
              variant="ghost"
              disabled={archive.isPending}
              onClick={() => archive.mutate(c.id)}
            >
              В архив
            </Button>
          </div>
        ))}
      </State>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <div className="form-grid">
          {(["full_name", "position", "email", "phone"] as const).map((k) => (
            <Field
              key={k}
              label={
                {
                  full_name: "ФИО",
                  position: "Должность",
                  email: "Email",
                  phone: "Телефон",
                }[k]
              }
            >
              <input
                required={k === "full_name"}
                type={k === "email" ? "email" : k === "phone" ? "tel" : "text"}
                value={form[k] || ""}
                onChange={(e) => setForm({ ...form, [k]: e.target.value })}
              />
            </Field>
          ))}
        </div>
        <Button disabled={!form.full_name.trim() || create.isPending}>
          Добавить контакт
        </Button>
        <Failure error={create.error || archive.error} />
      </form>
    </Panel>
  );
}
