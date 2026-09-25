import { useState } from "react";
import { Heading } from "../App";
import type { Schema } from "../api/types";
import { api } from "../api/runtime";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
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
const columns: Record<string, string> = {
  group: "Группа",
  counterparty: "Контрагент",
  direction: "Направление",
  program: "Программа",
  product: "Продукт",
  stage: "Этап",
  owner: "Ответственный",
  contract: "Договор",
  license_valid_until: "Лицензия до",
  days_on_stage: "Дней на этапе",
  signals: "Сигналы",
};
export function ReportsPage() {
  const [form, setForm] = useState<Schema["ReportCreate"]>({
    format: "xlsx",
    encoding: "utf-8",
    columns: Object.keys(columns),
  });
  const q = useResource<Schema["ReportJobOut"][]>("/reports");
  const groups = useResource<Schema["CounterpartyGroupOut"][]>(
    "/counterparty-groups",
  );
  const users = useResource<Schema["UserOut"][]>("/users");
  const programs = useResource<Schema["ProgramRef"][]>("/programs");
  const products = useResource<Schema["ProductRef"][]>("/products");
  const directions = useResource<Schema["DirectionRef"][]>("/directions");
  const [universitySearch, setUniversitySearch] = useState("");
  const universities = useResource<Schema["Page_UniversityOut_"]>(
    "/universities",
    { search: universitySearch, page_size: 100 },
  );
  const template = groups.data?.find(
    (g) => g.id === form.group_id?.[0],
  )?.workflow_template_id;
  const process = useResource<Schema["WorkflowOut"]>(
    template ? `/workflows/${template}` : "/workflows/default",
  );
  const create = useAction(() =>
    api.send<Schema["ReportJobOut"]>("/reports", form),
  );
  return (
    <>
      <Heading
        eyebrow="АНАЛИТИКА"
        title="Отчёты"
        text="Подготовьте выгрузку для коллег. Отчёт строится в фоне, работу можно продолжать."
      />
      <Panel title="Новый отчёт">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <div className="form-grid">
            <Field label="Формат">
              <Select
                value={form.format}
                onChange={(e) =>
                  setForm({
                    ...form,
                    format: e.target.value as Schema["ReportCreate"]["format"],
                  })
                }
              >
                {["xlsx", "xls", "csv", "pdf", "json"].map((f) => (
                  <option key={f} value={f}>
                    {f.toUpperCase()}
                  </option>
                ))}
              </Select>
            </Field>
            {form.format === "csv" && (
              <Field label="Кодировка">
                <Select
                  value={form.encoding}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      encoding: e.target.value as "utf-8" | "windows-1251",
                    })
                  }
                >
                  <option value="utf-8">UTF-8</option>
                  <option value="windows-1251">Windows-1251</option>
                </Select>
              </Field>
            )}
            <Field label="С даты">
              <input
                type="date"
                onChange={(e) =>
                  setForm({ ...form, period_from: e.target.value || null })
                }
              />
            </Field>
            <Field label="По дату">
              <input
                type="date"
                min={form.period_from || ""}
                onChange={(e) =>
                  setForm({ ...form, period_to: e.target.value || null })
                }
              />
            </Field>
            <Field label="Группа">
              <Select
                value={form.group_id?.[0] || ""}
                onChange={(e) =>
                  setForm({
                    ...form,
                    group_id: e.target.value ? [e.target.value] : [],
                    stage_code: [],
                  })
                }
              >
                <option value="">Все группы</option>
                {groups.data?.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Ответственный">
              <Select
                value={form.owner_id?.[0] || ""}
                onChange={(e) =>
                  setForm({
                    ...form,
                    owner_id: e.target.value ? [e.target.value] : [],
                  })
                }
              >
                <option value="">Все сотрудники</option>
                {users.data?.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Поиск вуза">
              <input
                value={universitySearch}
                onChange={(e) => setUniversitySearch(e.target.value)}
                placeholder="Найти вуз в справочнике"
              />
            </Field>
            {(
              [
                ["university_id", "Вуз", universities.data?.items || []],
                ["direction_id", "Направление", directions.data || []],
                ["program_id", "Программа", programs.data || []],
                ["product_id", "Продукт", products.data || []],
              ] as const
            ).map(([key, label, options]) => (
              <Field key={key} label={label}>
                <Select
                  value={form[key]?.[0] || ""}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      [key]: e.target.value ? [e.target.value] : [],
                    })
                  }
                >
                  <option value="">Все</option>
                  {options.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.name}
                    </option>
                  ))}
                </Select>
              </Field>
            ))}
            <Field label="Этап">
              <Select
                value={form.stage_code?.[0] || ""}
                onChange={(e) =>
                  setForm({
                    ...form,
                    stage_code: e.target.value ? [e.target.value] : [],
                  })
                }
              >
                <option value="">Все этапы</option>
                {process.data?.stages.map((s) => (
                  <option key={s.id} value={s.code}>
                    {s.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Состояние">
              <Select
                value={form.status?.[0] || ""}
                onChange={(e) =>
                  setForm({
                    ...form,
                    status: e.target.value
                      ? [
                          e.target.value as NonNullable<
                            Schema["ReportCreate"]["status"]
                          >[number],
                        ]
                      : [],
                  })
                }
              >
                <option value="">Все, кроме отменённых</option>
                {["active", "paused", "completed", "cancelled"].map((k) => (
                  <option key={k} value={k}>
                    {names[k]}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Поиск">
              <input
                placeholder="Вуз, программа, продукт"
                value={form.search || ""}
                onChange={(e) => setForm({ ...form, search: e.target.value })}
              />
            </Field>
          </div>
          <fieldset className="column-picker">
            <legend>Колонки в файле</legend>
            {Object.entries(columns).map(([key, label]) => (
              <label key={key}>
                <input
                  type="checkbox"
                  checked={form.columns?.includes(key)}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      columns: e.target.checked
                        ? [...(form.columns || []), key]
                        : form.columns?.filter((c) => c !== key),
                    })
                  }
                />
                {label}
              </label>
            ))}
          </fieldset>
          <Failure error={create.error} />
          <Button disabled={create.isPending || !form.columns?.length}>
            {create.isPending ? "Создаём задание…" : "Сформировать отчёт"}
          </Button>
          {create.isSuccess && (
            <p role="status">Задание создано. Готовый файл появится ниже.</p>
          )}
        </form>
      </Panel>
      <Panel
        title="Ваши выгрузки"
        action={
          <Button variant="ghost" onClick={() => void q.refetch()}>
            Обновить
          </Button>
        }
      >
        <State query={q}>
          {q.data?.map((r) => (
            <article className="service-row" key={r.id}>
              <span className="file-tile">{r.format.toUpperCase()}</span>
              <div className="grow">
                <h3>Отчёт от {when(r.created_at)}</h3>
                <p>
                  {names[r.status] || r.status} · {r.row_count ?? "—"} строк
                </p>
                {["running", "queued"].includes(r.status) && (
                  <progress max="100" value={r.progress} />
                )}{" "}
                {r.error_code && (
                  <p className="error-copy">
                    {r.error_code}. Попробуйте сформировать отчёт повторно.
                  </p>
                )}
              </div>
              {r.status === "done" && (
                <Download
                  path={`/reports/${r.id}/file`}
                  name={`Отчёт.${r.format}`}
                />
              )}
            </article>
          ))}
          {q.data && !q.data.length && <EmptyData />}
        </State>
      </Panel>
    </>
  );
}
