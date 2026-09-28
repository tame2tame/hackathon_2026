import { useState } from "react";
import type { Me, Schema } from "../api/types";
import { api } from "../api/runtime";
import { Button } from "../components/ui/button";
import {
  EmptyData,
  Failure,
  Field,
  Panel,
  State,
  useAction,
  useResource,
} from "./shared";
const channels = { email: "Почта", telegram: "Telegram", phone: "Телефон" };

export function VendorRow({
  vendor,
  me,
}: {
  vendor: Schema["VendorOut"];
  me: Me;
}) {
  const [open, setOpen] = useState(false);
  const archive = useAction(() =>
    api.send(`/admin/catalogs/vendors/${vendor.id}/archive`),
  );
  return (
    <div>
      <div
        className="service-row"
        style={vendor.archived_at ? { opacity: 0.6 } : undefined}
      >
        <div className="grow">
          <h3>
            {vendor.name}
            {vendor.archived_at && " · В архиве"}
          </h3>
          <small>ID: {vendor.id}</small>
          <p>
            {vendor.products.map((p) => p.name).join(", ") || "Нет продуктов"} ·
            Контактов: {vendor.contacts}
          </p>
        </div>
        {me.role === "admin" && !vendor.archived_at && (
          <Button
            variant="ghost"
            disabled={archive.isPending}
            onClick={() => archive.mutate()}
          >
            В архив
          </Button>
        )}
        <Button
          variant="outline"
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          {open ? "Скрыть контакты" : "Показать контакты"}
        </Button>
      </div>
      <Failure error={archive.error} />
      {open && <VendorContacts vendor={vendor} me={me} />}
    </div>
  );
}
export function VendorContacts({
  vendor,
  me,
}: {
  vendor: Schema["VendorOut"];
  me: Me;
}) {
  const q = useResource<Schema["VendorContactOut"][]>(
    `/vendors/${vendor.id}/contacts`,
  );
  const [form, setForm] = useState<Schema["VendorContactCreate"]>({
    full_name: "",
    channels: [],
    product_ids: [],
  });
  const create = useAction(async () => {
    const result = await api.send(`/vendors/${vendor.id}/contacts`, {
      ...form,
      full_name: form.full_name.trim(),
      email: form.email || null,
      phone: form.phone || null,
    });
    setForm({ full_name: "", channels: [], product_ids: [] });
    return result;
  });
  const archive = useAction((id: string) =>
    api.send(`/vendor-contacts/${id}/archive`),
  );
  const canEdit = me.role !== "kam" && !vendor.archived_at;
  return (
    <Panel title={`Контакты: ${vendor.name}`}>
      <State query={q}>
        {!q.data?.length && <EmptyData />}
        {q.data?.map((c) => (
          <div className="service-row" key={c.id}>
            <div className="grow">
              <h3>{c.full_name}</h3>
              <p>
                {c.email || "Почта не указана"} ·{" "}
                {c.phone || "Телефон не указан"}
              </p>
              <small>
                Каналы:{" "}
                {c.channels.map((v) => channels[v]).join(", ") || "Не указаны"}
              </small>
              <p>
                Продукты:{" "}
                {c.products.map((p) => p.name).join(", ") || "Не указаны"}
              </p>
            </div>
            {canEdit && (
              <Button
                variant="ghost"
                disabled={archive.isPending}
                onClick={() => archive.mutate(c.id)}
              >
                В архив
              </Button>
            )}
          </div>
        ))}
      </State>
      <Failure error={archive.error} />
      {canEdit && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <div className="form-grid">
            {(["full_name", "email", "phone"] as const).map((key) => (
              <Field
                key={key}
                label={
                  {
                    full_name: "ФИО контакта",
                    email: "Почта контакта",
                    phone: "Телефон контакта",
                  }[key]
                }
              >
                <input
                  type={
                    key === "email" ? "email" : key === "phone" ? "tel" : "text"
                  }
                  required={key === "full_name"}
                  minLength={key === "full_name" ? 2 : undefined}
                  maxLength={
                    key === "full_name" ? 200 : key === "email" ? 254 : 40
                  }
                  value={form[key] || ""}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              </Field>
            ))}
          </div>
          <fieldset>
            <legend>Предпочтительные каналы связи</legend>
            {(Object.keys(channels) as (keyof typeof channels)[]).map((key) => (
              <label key={key}>
                <input
                  type="checkbox"
                  checked={form.channels?.includes(key) || false}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      channels: e.target.checked
                        ? [...(form.channels || []), key]
                        : form.channels?.filter((v) => v !== key),
                    })
                  }
                />{" "}
                {channels[key]}{" "}
              </label>
            ))}
          </fieldset>
          <fieldset>
            <legend>Продукты контакта</legend>
            {vendor.products.length ? (
              vendor.products.map((p) => (
                <label key={p.id}>
                  <input
                    type="checkbox"
                    checked={form.product_ids?.includes(p.id) || false}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        product_ids: e.target.checked
                          ? [...(form.product_ids || []), p.id]
                          : form.product_ids?.filter((v) => v !== p.id),
                      })
                    }
                  />{" "}
                  {p.name}{" "}
                </label>
              ))
            ) : (
              <p>У вендора пока нет продуктов.</p>
            )}
          </fieldset>
          <Button
            disabled={create.isPending || form.full_name.trim().length < 2}
          >
            Добавить контакт
          </Button>
          <Failure error={create.error} />
          {create.isSuccess && <p role="status">Контакт добавлен.</p>}
        </form>
      )}
    </Panel>
  );
}
