import { useState } from "react";
import { api } from "../api/runtime";
import type { Interaction, Schema } from "../api/types";
import { Button } from "../components/ui/button";
import { Select } from "../components/ui/select";
import {
  Download,
  EmptyData,
  Failure,
  Field,
  Panel,
  State,
  names,
  when,
  useAction,
  useResource,
} from "./shared";
export function Documents({
  id,
  onUploaded,
}: {
  id: string;
  onUploaded?: (a: Schema["AttachmentOut"]) => void;
}) {
  const q = useResource<Schema["AttachmentOut"][]>(
    `/interactions/${id}/attachments`,
  );
  const [file, setFile] = useState<File | null>(null);
  const [type, setType] = useState("");
  const upload = useAction(async () => {
    const body = new FormData();
    body.append("file", file!);
    if (type) body.append("document_type", type);
    const a = await api.upload<Schema["AttachmentOut"]>(
      `/api/v1/interactions/${id}/attachments`,
      body,
    );
    onUploaded?.(a);
    return a;
  });
  return (
    <>
      <div className="form-grid">
        <Field label="Документ (до 25 МБ)">
          <input
            type="file"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.png,.jpg,.jpeg,.txt,.csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </Field>
        <Field label="Тип документа">
          <Select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="">Другой документ</option>
            <option value="signed_contract">Подписанный договор</option>
            <option value="transfer_act">Акт передачи материалов</option>
            <option value="training_confirmation">
              Подтверждение обучения
            </option>
            <option value="signed_offer">Подписанная оферта</option>
            <option value="payment_confirmation">Подтверждение оплаты</option>
            <option value="certificate">Сертификат</option>
          </Select>
        </Field>
      </div>
      <Button
        type="button"
        disabled={!file || file.size > 25 * 1024 * 1024 || upload.isPending}
        onClick={() => upload.mutate()}
      >
        {upload.isPending ? "Загружаем…" : "Загрузить документ"}
      </Button>
      {file && file.size > 25 * 1024 * 1024 && (
        <p className="error-copy">Файл превышает 25 МБ.</p>
      )}
      <Failure error={upload.error} />
      <State query={q}>
        {q.data?.map((a) => (
          <div className="service-row" key={a.id}>
            <div className="grow">
              <h3>{a.file_name}</h3>
              <small>
                {(a.size_bytes / 1024).toFixed(0)} КБ · {when(a.uploaded_at)}
              </small>
            </div>
            {onUploaded && (
              <Button
                type="button"
                variant="ghost"
                onClick={() => onUploaded(a)}
              >
                Прикрепить к переходу
              </Button>
            )}
            <Download path={`/attachments/${a.id}/file`} name={a.file_name} />
          </div>
        ))}
        {!q.data?.length && <EmptyData />}
      </State>
    </>
  );
}
export function RecordTools({ card }: { card: Interaction }) {
  const [tab, setTab] = useState("notes");
  return (
    <Panel title="Работа с записью">
      <div className="service-tabs">
        {Object.entries({
          notes: "Заметки",
          participants: "Обучающиеся и преподаватели",
          status: "Состояние и ответственный",
        }).map(([k, v]) => (
          <button
            key={k}
            className={tab === k ? "active" : ""}
            onClick={() => setTab(k)}
          >
            {v}
          </button>
        ))}
      </div>
      {tab === "notes" ? (
        <Notes id={card.id} />
      ) : tab === "participants" ? (
        <Participants id={card.id} />
      ) : (
        <RecordStatus card={card} />
      )}
    </Panel>
  );
}
function Notes({ id }: { id: string }) {
  const q = useResource<Schema["NoteOut"][]>(`/interactions/${id}/notes`);
  const [text, setText] = useState("");
  const add = useAction(async () => {
    const n = await api.send(`/interactions/${id}/notes`, { text });
    setText("");
    return n;
  });
  return (
    <>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          add.mutate();
        }}
      >
        <Field label="Новая заметка">
          <textarea
            required
            maxLength={4000}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Договорённости, следующий шаг, важные детали"
          />
        </Field>
        <Button disabled={!text.trim() || add.isPending}>
          Добавить заметку
        </Button>
        <Failure error={add.error} />
      </form>
      <State query={q}>
        {q.data?.map((n) => (
          <article className="service-row" key={n.id}>
            <div>
              <p>{n.text}</p>
              <small>
                {n.author.full_name} · {when(n.created_at)}
              </small>
            </div>
          </article>
        ))}
      </State>
    </>
  );
}
function RecordStatus({ card }: { card: Interaction }) {
  const [status, setStatus] = useState(card.status);
  const [reason, setReason] = useState("");
  const [owner, setOwner] = useState(card.owner.id);
  const users = useResource<Schema["UserOut"][]>("/users");
  const me = useResource<Schema["MeOut"]>("/me");
  const change = useAction(() =>
    api.send(
      `/interactions/${card.id}/status`,
      { status, reason, expected_version: card.version },
      "PUT",
    ),
  );
  const reassign = useAction(() =>
    api.send(
      `/interactions/${card.id}/owner`,
      { owner_id: owner, reason, expected_version: card.version },
      "PUT",
    ),
  );
  return (
    <>
      <div className="form-grid">
        <Field label="Состояние">
          <Select value={status} onChange={(e) => setStatus(e.target.value)}>
            {["active", "paused", "completed", "cancelled"].map((k) => (
              <option key={k} value={k}>
                {names[k]}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Причина">
          <input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Почему меняется состояние?"
          />
        </Field>
      </div>
      <Button
        disabled={
          change.isPending ||
          status === card.status ||
          (["paused", "cancelled"].includes(status) && !reason.trim())
        }
        onClick={() => change.mutate()}
      >
        Изменить состояние
      </Button>
      <Failure error={change.error} />
      {me.data && me.data.role !== "kam" && (
        <>
          <div className="service-toolbar">
            <Field label="Ответственный">
              <Select value={owner} onChange={(e) => setOwner(e.target.value)}>
                {users.data?.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name}
                  </option>
                ))}
              </Select>
            </Field>
            <Button
              disabled={
                reassign.isPending || owner === card.owner.id || !reason.trim()
              }
              onClick={() => reassign.mutate()}
            >
              Передать запись
            </Button>
          </div>
          <Failure error={reassign.error} />
        </>
      )}
      <Download
        path={`/interactions/${card.id}/export`}
        name="Взаимодействие.json"
      >
        Выгрузить запись
      </Download>
    </>
  );
}
export function Participants({ id }: { id: string }) {
  const q = useResource<Schema["ParticipantsOut"]>(
    `/interactions/${id}/participants`,
  );
  const [form, setForm] = useState<Schema["ParticipantCreate"]>({
    role: "student",
    full_name: "",
  });
  const add = useAction(async () => {
    const r = await api.send(`/interactions/${id}/participants`, form);
    setForm({ role: "student", full_name: "" });
    return r;
  });
  return (
    <>
      <div className="service-toolbar">
        <span>
          Обучающихся: {q.data?.counts.students ?? "…"} · Преподавателей:{" "}
          {q.data?.counts.teachers ?? "…"}
        </span>
        <Download
          path={`/interactions/${id}/participants/export?format=xlsx`}
          name="Участники.xlsx"
        />
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          add.mutate();
        }}
      >
        <div className="form-grid">
          <Field label="ФИО">
            <input
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </Field>
          <Field label="Роль">
            <Select
              value={form.role}
              onChange={(e) =>
                setForm({
                  ...form,
                  role: e.target.value as "student" | "teacher",
                })
              }
            >
              <option value="student">Обучающийся</option>
              <option value="teacher">Преподаватель</option>
            </Select>
          </Field>
          <Field label="Email">
            <input
              type="email"
              value={form.email || ""}
              onChange={(e) =>
                setForm({ ...form, email: e.target.value || null })
              }
            />
          </Field>
        </div>
        <Button disabled={!form.full_name.trim() || add.isPending}>
          Добавить участника
        </Button>
        <Failure error={add.error} />
      </form>
      <State query={q}>
        {q.data?.items.map((p) => (
          <Participant key={p.id} item={p} />
        ))}
      </State>
      <FilePreview path={`/interactions/${id}/participants/import`} />
    </>
  );
}
function Participant({ item: p }: { item: Schema["ParticipantOut"] }) {
  const [reveal, setReveal] = useState(false);
  const contact = useResource<Schema["ParticipantContactOut"]>(
    `/participants/${p.id}/contact`,
    {},
    reveal,
  );
  return (
    <div className="service-row">
      <div className="grow">
        <h3>{p.full_name}</h3>
        <small>
          {p.role === "student" ? "Обучающийся" : "Преподаватель"} ·{" "}
          {contact.data?.email || p.email || "Нет email"}
        </small>
      </div>
      {p.has_email && (
        <Button variant="ghost" onClick={() => setReveal(true)}>
          Показать контакт
        </Button>
      )}
      <Failure error={contact.error} />
    </div>
  );
}
export function FilePreview({ path }: { path: string }) {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<Schema["ParticipantImportOut"] | null>(
    null,
  );
  const action = useAction(async (dry: boolean) => {
    const body = new FormData();
    body.append("file", file!);
    body.append("dry_run", String(dry));
    const r = await api.upload<Schema["ParticipantImportOut"]>(
      "/api/v1" + path,
      body,
    );
    setResult(r);
    return r;
  });
  return (
    <details className="file-import">
      <summary>Загрузить участников из таблицы</summary>
      <Field label="Файл">
        <input
          type="file"
          accept=".csv,.xls,.xlsx,.json"
          onChange={(e) => {
            setFile(e.target.files?.[0] || null);
            setResult(null);
          }}
        />
      </Field>
      <Button
        disabled={!file || action.isPending}
        onClick={() => action.mutate(true)}
      >
        Проверить
      </Button>
      {result?.rows.map((r) => (
        <p key={r.row_no}>
          {r.row_no}. {r.key}: {names[r.action]} {r.detail}
        </p>
      ))}
      {result?.dry_run && (
        <Button
          disabled={action.isPending}
          onClick={() => action.mutate(false)}
        >
          Применить
        </Button>
      )}
      {result && !result.dry_run && <p role="status">Изменения применены.</p>}
      <Failure error={action.error} />
    </details>
  );
}
