import { Link } from "react-router-dom";
import { useState } from "react";
import type { Me, Schema } from "../api/types";
import { api } from "../api/runtime";
import { queryString } from "../api/client";
import { Button } from "../components/ui/button";
import { Select } from "../components/ui/select";
import {
  Download,
  Failure,
  Field,
  Panel,
  State,
  names,
  useAction,
  useResource,
} from "./shared";

export function Payments({ me }: { me: Me }) {
  const [file, setFile] = useState<File | null>(null);
  const [encoding, setEncoding] = useState("");
  const [preview, setPreview] = useState<Schema["PaymentImportOut"] | null>(
    null,
  );
  const [program, setProgram] = useState("");
  const [stream, setStream] = useState("");
  const groups = useResource<Schema["CounterpartyGroupOut"][]>(
    "/counterparty-groups",
  );
  const b2c = groups.data?.find((g) => g.code === "b2c");
  const programs = useResource<Schema["ProgramRef"][]>("/programs");
  const upload = useAction(async (dry: boolean) => {
    const body = new FormData();
    body.append("file", file!);
    body.append("dry_run", String(dry));
    if (encoding) body.append("encoding", encoding);
    setPreview(null);
    const result = await api.upload<Schema["PaymentImportOut"]>(
      "/api/v1/payments/import",
      body,
    );
    setPreview(result);
    return result;
  });
  return (
    <Panel title="Частные лица: оплаты и зачисление в LMS">
      {me.role !== "kam" && (
        <>
          <p>
            Загрузите выгрузку платёжной системы. После применения оплаты записи
            переходят на этап «Зачисление в LMS».
          </p>
          <div className="form-grid">
            <Field label="Файл оплат (JSON, CSV, XLSX, XLS)">
              <input
                type="file"
                accept=".json,.csv,.xlsx,.xls"
                disabled={upload.isPending}
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null);
                  setPreview(null);
                  upload.reset();
                }}
              />
            </Field>
            <Field label="Кодировка CSV">
              <Select
                value={encoding}
                disabled={upload.isPending}
                onChange={(e) => {
                  setEncoding(e.target.value);
                  setPreview(null);
                  upload.reset();
                }}
              >
                <option value="">Определить автоматически</option>
                {["utf-8", "windows-1251", "koi8-r", "cp866", "utf-16"].map(
                  (v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ),
                )}
              </Select>
            </Field>
          </div>
          <div className="service-toolbar">
            <Button
              disabled={!file || upload.isPending}
              onClick={() => upload.mutate(true)}
            >
              Проверить оплаты
            </Button>
            {preview?.dry_run && (
              <Button
                disabled={upload.isPending}
                onClick={() => upload.mutate(false)}
              >
                Применить оплаты
              </Button>
            )}
          </div>
          <Failure error={upload.error} />
          {preview && (
            <>
              <p role="status">
                {preview.dry_run ? "Предпросмотр оплат" : "Оплаты применены"}:
                новых — {preview.created}, обновлено — {preview.updated}, без
                изменений — {preview.unchanged}, ошибок — {preview.errors}.
              </p>
              <div className="table-scroll">
                <table className="service-table">
                  <thead>
                    <tr>
                      <th>Строка</th>
                      <th>Номер заявки</th>
                      <th>Результат</th>
                      <th>Причина</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.rows.map((r) => (
                      <tr key={r.row_no}>
                        <td>{r.row_no}</td>
                        <td>{r.key}</td>
                        <td>
                          <span
                            className={
                              r.action === "error" ? "service-error" : "badge"
                            }
                          >
                            {names[r.action]}
                          </span>
                        </td>
                        <td>{r.detail || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
      {b2c && (
        <Link
          to={
            "/interactions" +
            queryString({ group: b2c.id, stage: "enrollment" })
          }
        >
          Открыть записи на этапе «Зачисление в LMS»
        </Link>
      )}
      <h3>Загрузка пользователей в LMS</h3>
      <p>
        В XLSX попадут доступные вам частные лица на этапе «Зачисление в LMS».
        Курс и поток можно не указывать.
      </p>
      <State query={programs}>
        <div className="form-grid">
          <Field label="Курс для LMS">
            <Select
              value={program}
              onChange={(e) => setProgram(e.target.value)}
            >
              <option value="">Все курсы</option>
              {programs.data?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Номер потока">
            <input
              type="number"
              min="1"
              step="1"
              value={stream}
              onChange={(e) => setStream(e.target.value)}
            />
          </Field>
        </div>
      </State>
      {!stream || (Number.isInteger(Number(stream)) && Number(stream) >= 1) ? (
        <Download
          path={
            "/payments/lms-users" + queryString({ program_id: program, stream })
          }
          name="Загрузка пользователей.xlsx"
        >
          Скачать пользователей для LMS
        </Download>
      ) : (
        <p role="alert">Номер потока должен быть целым числом от 1.</p>
      )}
    </Panel>
  );
}
