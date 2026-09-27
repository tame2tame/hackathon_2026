import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as Dialog from "@radix-ui/react-dialog";
import { api } from "../api/runtime";
import type { Schema } from "../api/types";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
import { Failure, Field, useAction, useResource } from "./shared";
export function CreateRecord() {
  const [open, setOpen] = useState(false);
  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button>Новое взаимодействие +</Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content">
          <Dialog.Title>Новое взаимодействие</Dialog.Title>
          <Dialog.Description>
            Выберите контрагента, программу и ответственного.
          </Dialog.Description>
          <CreateForm close={() => setOpen(false)} />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
function CreateForm({ close }: { close: () => void }) {
  const navigate = useNavigate();
  const groups = useResource<Schema["CounterpartyGroupOut"][]>(
    "/counterparty-groups",
  );
  const programs = useResource<Schema["ProgramRef"][]>("/programs");
  const products = useResource<Schema["ProductRef"][]>("/products");
  const users = useResource<Schema["UserOut"][]>("/users");
  const [kind, setKind] = useState("university");
  const [search, setSearch] = useState("");
  const universities = useResource<Schema["Page_UniversityOut_"]>(
    "/universities",
    { search, page_size: 100 },
    kind === "university",
  );
  const clients = useResource<Schema["Page_ClientListItem_"]>(
    "/clients",
    { search, page_size: 100 },
    kind === "client",
  );
  const [form, setForm] = useState<Schema["InteractionCreate"]>({
    group_id: "",
    program_id: "",
    comment: "",
  });
  const create = useAction(async () => {
    const r = await api.send<Schema["InteractionDetail"]>(
      "/interactions",
      form,
    );
    close();
    navigate(`/interactions/${r.id}`);
    return r;
  });
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        create.mutate();
      }}
    >
      <div className="form-grid">
        <Field label="Группа">
          <Select
            value={form.group_id}
            onChange={(e) => setForm({ ...form, group_id: e.target.value })}
          >
            <option value="">Выберите группу</option>
            {groups.data?.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Тип контрагента">
          <Select
            value={kind}
            onChange={(e) => {
              setKind(e.target.value);
              setForm({ ...form, university_id: null, client_id: null });
            }}
          >
            <option value="university">Вуз</option>
            <option value="client">Клиент</option>
          </Select>
        </Field>
        <Field label="Поиск контрагента">
          <input value={search} onChange={(e) => setSearch(e.target.value)} />
        </Field>
        <Field label="Контрагент">
          <Select
            value={form.university_id || form.client_id || ""}
            onChange={(e) =>
              setForm({
                ...form,
                [kind === "university" ? "university_id" : "client_id"]:
                  e.target.value,
              })
            }
          >
            <option value="">Выберите контрагента</option>
            {(kind === "university"
              ? universities.data?.items
              : clients.data?.items
            )?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Программа">
          <Select
            value={form.program_id}
            onChange={(e) =>
              setForm({ ...form, program_id: e.target.value, product_id: null })
            }
          >
            <option value="">Выберите программу</option>
            {programs.data?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Продукт">
          <Select
            value={form.product_id || ""}
            onChange={(e) =>
              setForm({ ...form, product_id: e.target.value || null })
            }
          >
            <option value="">Без продукта</option>
            {products.data?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Ответственный">
          <Select
            value={form.owner_id || ""}
            onChange={(e) =>
              setForm({ ...form, owner_id: e.target.value || null })
            }
          >
            <option value="">Назначить на меня</option>
            {users.data?.map((u) => (
              <option key={u.id} value={u.id}>
                {u.full_name}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <Field label="Комментарий">
        <textarea
          value={form.comment}
          maxLength={4000}
          onChange={(e) => setForm({ ...form, comment: e.target.value })}
        />
      </Field>
      <Failure error={create.error} />
      <div className="dialog-actions">
        <Button type="button" variant="outline" onClick={close}>
          Отмена
        </Button>
        <Button
          disabled={
            !form.group_id ||
            !form.program_id ||
            !(form.university_id || form.client_id) ||
            create.isPending
          }
        >
          Создать
        </Button>
      </div>
    </form>
  );
}
