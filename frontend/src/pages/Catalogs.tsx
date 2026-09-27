import { Groups } from "./Groups";
import { useState } from "react";
import { Heading } from "../App";
import { api } from "../api/runtime";
import type { Me, Schema } from "../api/types";
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
  Pager,
} from "./shared";
const catalogs: Record<string, string> = {
  groups: "Группы контрагентов",
  universities: "Вузы",
  directions: "Направления",
  programs: "Программы",
  vendors: "Вендоры",
  products: "Продукты",
  "program-products": "Программы и продукты",
};
export function CatalogsPage({ me }: { me: Me }) {
  const [kind, setKind] = useState("universities");
  return (
    <>
      <Heading
        eyebrow="АДМИНИСТРИРОВАНИЕ"
        title="Каталоги"
        text="Единые справочники для записей, аналитики и импорта."
      />
      <div className="service-tabs">
        {Object.entries(catalogs).map(([k, v]) => (
          <button
            key={k}
            className={kind === k ? "active" : ""}
            onClick={() => setKind(k)}
          >
            {v}
          </button>
        ))}
      </div>
      {kind === "groups" ? (
        <Groups me={me} />
      ) : (
        <Catalog key={kind} kind={kind} me={me} />
      )}
    </>
  );
}
function Catalog({ kind, me }: { kind: string; me: Me }) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState<Record<string, string>>({ name: "" });
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Schema["CatalogImportOut"] | null>(
    null,
  );
  const [archived, setArchived] = useState(false);
  const q = useResource<
    | Schema["Page_UniversityOut_"]
    | Schema["ProgramRef"][]
    | Schema["DirectionRef"][]
    | Schema["ProductRef"][]
  >(
    kind === "vendors" || kind === "program-products"
      ? "/products"
      : "/" + kind,
    { page, page_size: 20, search: search || undefined },
  );
  const directions = useResource<Schema["DirectionRef"][]>(
    "/directions",
    {},
    kind === "programs",
  );
  const products = useResource<Schema["ProductRef"][]>(
    "/products",
    {},
    kind === "products" || kind === "vendors",
  );
  const vendors = Array.from(
    new Map(products.data?.map((p) => [p.vendor.id, p.vendor]) || []).values(),
  );
  let rows = q.data ? (Array.isArray(q.data) ? q.data : q.data.items) : [];
  if (kind === "vendors") rows = vendors as typeof rows;
  const create = useAction(async () => {
    const r = await api.send(`/admin/catalogs/${kind}`, form);
    setForm({ name: "" });
    return r;
  });
  const archive = useAction((id: string) =>
    api.send(`/admin/catalogs/${kind}/${id}/archive`),
  );
  const upload = useAction(async (dry: boolean) => {
    const body = new FormData();
    body.append("file", file!);
    body.append("dry_run", String(dry));
    const r = await api.upload<Schema["CatalogImportOut"]>(
      `/api/v1/admin/catalogs/${kind}/import`,
      body,
    );
    setPreview(r);
    return r;
  });
  return (
    <>
      <Panel
        title={catalogs[kind]}
        action={
          me.role === "admin" ? (
            <Download
              path={`/admin/catalogs/${kind}/export?format=xlsx&include_archived=${archived}`}
              name={`${catalogs[kind]}.xlsx`}
            >
              Выгрузить XLSX
            </Download>
          ) : undefined
        }
      >
        {kind === "universities" && (
          <Field label="Поиск">
            <input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </Field>
        )}
        <State query={q}>
          {kind === "program-products" ? (
            <p>
              Связи программ и продуктов загружаются и выгружаются таблицей.
              Используйте выгрузку как шаблон для изменения связей.
            </p>
          ) : (
            rows
              .filter(
                (r) =>
                  kind === "universities" ||
                  r.name.toLowerCase().includes(search.toLowerCase()),
              )
              .map((r) => (
                <div className="service-row" key={r.id}>
                  <div className="grow">
                    <h3>{r.name}</h3>
                    {"direction" in r && <small>{r.direction.name}</small>}
                    {"region" in r && <small>{String(r.region || "")}</small>}
                  </div>
                  {me.role === "admin" && (
                    <Button
                      variant="ghost"
                      disabled={archive.isPending}
                      onClick={() => archive.mutate(r.id)}
                    >
                      В архив
                    </Button>
                  )}
                </div>
              ))
          )}
          {q.data && !Array.isArray(q.data) && (
            <Pager page={page} total={q.data.total} onPage={setPage} />
          )}
        </State>
        <Failure error={archive.error} />
      </Panel>
      {me.role === "admin" && (
        <>
          {kind !== "program-products" && (
            <Panel title="Добавить запись">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  create.mutate();
                }}
              >
                <div className="form-grid">
                  <Field label="Название">
                    <input
                      required
                      value={form.name}
                      onChange={(e) =>
                        setForm({ ...form, name: e.target.value })
                      }
                    />
                  </Field>
                  {(kind === "universities"
                    ? ["short_name", "region", "city"]
                    : kind === "directions"
                      ? ["code"]
                      : []
                  ).map((key) => (
                    <Field
                      key={key}
                      label={
                        {
                          short_name: "Краткое название",
                          region: "Регион",
                          city: "Город",
                          code: "Код направления",
                        }[key] || key
                      }
                    >
                      <input
                        value={form[key] || ""}
                        onChange={(e) =>
                          setForm({ ...form, [key]: e.target.value })
                        }
                      />
                    </Field>
                  ))}
                  {kind === "programs" && (
                    <Field label="Направление">
                      <Select
                        value={form.direction_id || ""}
                        onChange={(e) =>
                          setForm({ ...form, direction_id: e.target.value })
                        }
                      >
                        <option value="">Выберите направление</option>
                        {directions.data?.map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.name}
                          </option>
                        ))}
                      </Select>
                    </Field>
                  )}
                  {kind === "products" && (
                    <Field label="Вендор">
                      <Select
                        value={form.vendor_id || ""}
                        onChange={(e) =>
                          setForm({ ...form, vendor_id: e.target.value })
                        }
                      >
                        <option value="">Выберите вендора</option>
                        {vendors.map((v) => (
                          <option key={v.id} value={v.id}>
                            {v.name}
                          </option>
                        ))}
                      </Select>
                    </Field>
                  )}
                </div>
                <Button disabled={create.isPending}>Добавить</Button>
                <Failure error={create.error} />
              </form>
            </Panel>
          )}
          <Panel title="Загрузка из таблицы">
            <p>Сначала проверяем строки, затем применяем изменения.</p>
            <Field label="Файл XLSX, XLS или CSV">
              <input
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null);
                  setPreview(null);
                }}
              />
            </Field>
            <label>
              <input
                type="checkbox"
                checked={archived}
                onChange={(e) => setArchived(e.target.checked)}
              />{" "}
              Включать архивные записи в выгрузку
            </label>
            <div className="service-toolbar">
              <Button
                disabled={!file || upload.isPending}
                onClick={() => upload.mutate(true)}
              >
                Проверить файл
              </Button>
              {preview?.dry_run && (
                <Button
                  disabled={upload.isPending}
                  onClick={() => upload.mutate(false)}
                >
                  Применить
                </Button>
              )}
            </div>
            <Failure error={upload.error} />
            {preview && (
              <>
                <p role="status">
                  {preview.dry_run ? "Предпросмотр" : "Изменения применены"}
                </p>
                {preview.rows.map((r) => (
                  <div className="service-row" key={r.row_no}>
                    <span>{r.row_no}</span>
                    <strong>{r.key}</strong>
                    <span>{names[r.action]}</span>
                    <small>{r.detail}</small>
                  </div>
                ))}
              </>
            )}
          </Panel>
        </>
      )}
    </>
  );
}
