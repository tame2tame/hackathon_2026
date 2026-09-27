import { useState } from "react";
import { Heading } from "../App";
import { api } from "../api/runtime";
import type { Schema } from "../api/types";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
import {
  Failure,
  Field,
  Panel,
  Summary,
  names,
  useAction,
  useResource,
} from "./shared";
const fieldNames: Record<string, string> = {
  university: "Вуз",
  university_name: "Название вуза",
  program: "Программа",
  program_name: "Программа",
  product: "Продукт",
  product_name: "Продукт",
  contract_number: "Номер договора",
  contract_date: "Дата договора",
  license_valid_until: "Лицензия до",
  stage: "Этап",
  stage_code: "Код этапа",
  owner_email: "Email ответственного",
  direction: "Направление",
  region: "Регион",
  city: "Город",
};
export function ImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [encoding, setEncoding] = useState("");
  const [batch, setBatch] = useState<Schema["ImportBatchOut"] | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState(false);
  const [profile, setProfile] = useState("");
  const profiles =
    useResource<Schema["ImportProfileOut"][]>("/import-profiles");
  const upload = useAction(async () => {
    const body = new FormData();
    body.append("file", file!);
    if (encoding) body.append("encoding", encoding);
    const b = await api.upload<Schema["ImportBatchOut"]>(
      "/api/v1/imports",
      body,
    );
    setBatch(b);
    setMapping(b.suggested_map);
    setPreview(false);
    return b;
  });
  const map = useAction(async () => {
    const b = await api.send<Schema["ImportBatchOut"]>(
      `/imports/${batch!.id}/mapping`,
      {
        column_map: Object.fromEntries(
          Object.entries(mapping).filter(([, v]) => v),
        ),
        save_as_profile: profile || null,
      },
      "PUT",
    );
    setBatch(b);
    setPreview(true);
    return b;
  });
  const apply = useAction(async () => {
    return api.send<Schema["ApplyResult"]>(`/imports/${batch!.id}/apply`);
  });
  return (
    <>
      <Heading
        eyebrow="УПРАВЛЕНИЕ"
        title="Импорт данных"
        text="Загрузите таблицу, проверьте соответствие колонок и примените изменения."
      />
      <ol className="wizard-steps">
        {["Файл", "Колонки", "Проверка и применение"].map((s, i) => (
          <li
            key={s}
            className={(preview ? 2 : batch ? 1 : 0) === i ? "active" : ""}
          >
            <b>{i + 1}</b>
            {s}
          </li>
        ))}
      </ol>
      <Panel title="1. Исходный файл">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            upload.mutate();
          }}
          className="service-toolbar"
        >
          <Field label="Таблица XLSX, XLS или CSV">
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              required
              onChange={(e) => {
                setFile(e.target.files?.[0] || null);
                setBatch(null);
                setPreview(false);
                apply.reset();
              }}
            />
          </Field>
          <Field label="Кодировка CSV">
            <Select
              value={encoding}
              onChange={(e) => setEncoding(e.target.value)}
            >
              <option value="">Определить автоматически</option>
              <option value="utf-8">UTF-8</option>
              <option value="windows-1251">Windows-1251</option>
              <option value="koi8-r">KOI8-R</option>
              <option value="cp866">CP866</option>
            </Select>
          </Field>
          <Button disabled={!file || upload.isPending}>
            {upload.isPending ? "Читаем файл…" : "Загрузить"}
          </Button>
        </form>
        <Failure error={upload.error} />
      </Panel>
      {batch && (
        <>
          <Panel title="2. Соответствие колонок">
            <p>
              {batch.file_name} · {batch.total_rows} строк ·{" "}
              {batch.encoding || batch.file_kind} · разделитель:{" "}
              {batch.delimiter || "—"}
            </p>
            <Field label="Сохранённый профиль">
              <Select
                value=""
                onChange={(e) => {
                  const p = profiles.data?.find((p) => p.id === e.target.value);
                  if (p) {
                    setMapping(p.column_map);
                    setPreview(false);
                  }
                }}
              >
                <option value="">Выберите профиль</option>
                {profiles.data?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </Select>
            </Field>
            <div className="form-grid">
              {batch.fields.map((field) => (
                <Field
                  key={field}
                  label={`${fieldNames[field] || field}${batch.required_fields.includes(field) ? " *" : ""}`}
                >
                  <Select
                    value={mapping[field] || ""}
                    onChange={(e) => {
                      setMapping({ ...mapping, [field]: e.target.value });
                      setPreview(false);
                    }}
                  >
                    <option value="">Не загружать</option>
                    {batch.headers.map((h) => (
                      <option key={h} value={h}>
                        {h}
                      </option>
                    ))}
                  </Select>
                </Field>
              ))}
            </div>
            <Field label="Сохранить профиль под именем (необязательно)">
              <input
                value={profile}
                onChange={(e) => setProfile(e.target.value)}
              />
            </Field>
            <Failure error={map.error} />
            <Button
              disabled={
                map.isPending ||
                batch.required_fields.some((f) => !mapping[f]) ||
                apply.isSuccess
              }
              onClick={() => map.mutate()}
            >
              Проверить строки
            </Button>
          </Panel>
          {preview && (
            <Panel title="3. Предпросмотр">
              <Summary stats={batch.stats} />
              <div className="table-scroll">
                <table className="service-table">
                  <thead>
                    <tr>
                      <th>Строка</th>
                      <th>Вуз</th>
                      <th>Продукт</th>
                      <th>Результат</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batch.rows.map((r) => (
                      <tr key={r.row_no}>
                        <td>{r.row_no}</td>
                        <td>{r.university}</td>
                        <td>{r.product}</td>
                        <td>
                          {names[r.resolution] || r.resolution}
                          <small>{r.detail}</small>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Failure error={apply.error} />
              <Button
                disabled={apply.isPending || apply.isSuccess}
                onClick={() => apply.mutate()}
              >
                {apply.isSuccess ? "Импорт применён" : "Применить импорт"}
              </Button>
              {apply.isSuccess && (
                <div role="status">
                  <p>
                    Изменения сохранены. Повторная загрузка не создаст
                    дубликаты.
                  </p>
                  {apply.data && (
                    <Summary
                      stats={{
                        created: apply.data.created,
                        updated: apply.data.updated,
                        skip: apply.data.skipped,
                        conflict: apply.data.conflicts,
                        needs_program: apply.data.needs_program,
                      }}
                    />
                  )}
                </div>
              )}
            </Panel>
          )}
        </>
      )}
    </>
  );
}
