import {
  useState,
  useEffect,
  useId,
  isValidElement,
  cloneElement,
  type ReactNode,
} from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/runtime";
import { ApiError } from "../api/client";
import { Button } from "../components/ui/button";
export const enc = encodeURIComponent;
export const when = (v?: string | null) =>
  v
    ? new Date(v).toLocaleString("ru-RU", {
        dateStyle: "short",
        timeStyle: "short",
      })
    : "—";
export const names: Record<string, string> = {
  applications: "Заявки",
  students: "Обучающиеся",
  streams: "Потоки",
  queued: "В очереди",
  running: "Выполняется",
  done: "Готово",
  failed: "Ошибка",
  new: "Новая",
  update: "Обновление",
  skip: "Пропущена",
  conflict: "Конфликт",
  needs_program: "Нужна программа",
  created: "Создано",
  updated: "Обновлено",
  unchanged: "Без изменений",
  error: "Ошибка",
  pending: "Ожидает",
  sent: "Отправлено",
  active: "В работе",
  paused: "Приостановлено",
  completed: "Завершено",
  cancelled: "Отменено",
};
export function Failure({ error }: { error: Error | null }) {
  return error ? (
    <div className="service-error" role="alert">
      <strong>{error.message}</strong>
      {error instanceof ApiError && (
        <>
          <small>
            {error.code}
            {error.traceId && ` · Код запроса: ${error.traceId}`}
          </small>
          {error.fields.map((f) => (
            <p key={f.field}>
              {f.field}: {f.message}
            </p>
          ))}
        </>
      )}
    </div>
  ) : null;
}
export function useResource<T>(
  path: string,
  params: object = {},
  enabled = true,
) {
  return useQuery({
    queryKey: ["service", path, params],
    queryFn: ({ signal }) => api.get<T>(path, params, signal),
    enabled,
  });
}
export function useAction<T, V = void>(fn: (value: V) => Promise<T>) {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      void cache.invalidateQueries();
    },
  });
}
export function State({
  query,
  children,
}: {
  query: { isPending: boolean; error: Error | null; refetch: () => unknown };
  children: ReactNode;
}) {
  if (query.error)
    return (
      <>
        <Failure error={query.error} />
        <Button variant="outline" onClick={() => void query.refetch()}>
          Повторить
        </Button>
      </>
    );
  if (query.isPending)
    return (
      <div className="service-loading" role="status">
        <div className="skeleton" />
        <p>Загружаем данные…</p>
      </div>
    );
  return <>{children}</>;
}
export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <label className="service-field" htmlFor={id}>
      <span>{label}</span>
      {isValidElement<{ id?: string; "aria-label"?: string }>(children)
        ? cloneElement(children, { id, "aria-label": label })
        : children}
    </label>
  );
}
export function Panel({
  title,
  children,
  action,
}: {
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <section className="panel service-panel">
      <div className="section-heading">
        <h2>{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}
export function EmptyData() {
  return (
    <div className="service-empty">
      Пока нет данных. Измените фильтры или добавьте первую запись.
    </div>
  );
}
export function Download({
  path,
  name,
  children = "Скачать",
}: {
  path: string;
  name: string;
  children?: ReactNode;
}) {
  const [error, setError] = useState<Error | null>(null);
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState<string | null>(null);
  useEffect(
    () => () => {
      if (ready) URL.revokeObjectURL(ready);
    },
    [ready],
  );
  useEffect(() => setReady(null), [path]);
  return (
    <div className="download-control">
      <Button
        type="button"
        variant="outline"
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          setError(null);
          try {
            const blob = await api.file(
              "/api/v1" + path,
              name.toLowerCase().endsWith(".pdf") ? "pdf" : undefined,
            );
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = name;
            a.click();
            setReady(url);
          } catch (e) {
            setError(e as Error);
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "Загрузка…" : children}
      </Button>
      {ready && (
        <span className="download-ready" role="status">
          Файл готов ·{" "}
          <a href={ready} download={name}>
            Скачать повторно
          </a>
          {name.endsWith(".pdf") && (
            <>
              {" "}
              ·{" "}
              <a href={ready} target="_blank" rel="noreferrer">
                Открыть PDF
              </a>
            </>
          )}
        </span>
      )}
      <Failure error={error} />
    </div>
  );
}
export function Pager({
  page,
  total,
  onPage,
}: {
  page: number;
  total: number;
  onPage: (n: number) => void;
}) {
  return (
    <div className="pagination">
      <span>Всего: {total}</span>
      <Button
        variant="outline"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
      >
        Назад
      </Button>
      <span>{page}</span>
      <Button
        variant="outline"
        disabled={page * 20 >= total}
        onClick={() => onPage(page + 1)}
      >
        Далее
      </Button>
    </div>
  );
}
export function Summary({ stats }: { stats: Record<string, unknown> }) {
  return (
    <div className="summary-chips">
      {Object.entries(stats).map(([k, v]) => (
        <span key={k}>
          {names[k] || k}: <strong>{String(v)}</strong>
        </span>
      ))}
    </div>
  );
}
