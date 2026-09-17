import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useParams,
} from "react-router-dom";
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import {
  Radar,
  Building2,
  Layers3,
  CircleHelp,
  ArrowRight,
  ArrowUpRight,
  ChevronRight,
  Search,
  X,
  RefreshCw,
  LogOut,
  ShieldCheck,
  Clock3,
  CalendarClock,
  FileWarning,
  CirclePause,
} from "lucide-react";
import { navigation, planned, Heading, Planned, Empty } from "./App";
import { Button } from "./components/ui/button";
import { roleNames, kinds } from "./lib/data";
import { api } from "./api/runtime";
import { ApiError } from "./api/client";
import { interactionQueryOptions } from "./api/queries";
import type {
  Me,
  Signal,
  Schema,
  Interaction as Card,
  InteractionFilters,
} from "./api/types";
import { mode } from "./auth/config";
import {
  currentDevUser,
  setDevUser,
  devUsers,
  initializeSession,
  login,
  logout,
} from "./auth/session";
const icons = {
  stage_overdue: Clock3,
  license_expiring: CalendarClock,
  missing_document: FileWarning,
  inactivity: CirclePause,
};
const labels = { high: "Высокий", medium: "Средний", low: "Низкий" };
const cleanCopy = (text: string) => text.replace(/\s[—–]\s/g, ", ");
const date = (value: string) =>
  new Date(value).toLocaleString("ru-RU", {
    dateStyle: "short",
    timeStyle: "short",
  });
export default function ConnectedApp() {
  const [auth, setAuth] = useState<"loading" | "ready" | "login" | "error">(
    "loading",
  );
  const [identity, setIdentity] = useState(currentDevUser);
  const [changing, setChanging] = useState(false);
  const client = useQueryClient();
  const location = useLocation();
  useEffect(() => {
    let active = true;
    initializeSession()
      .then((ok) => {
        if (active) setAuth(ok ? "ready" : "login");
      })
      .catch(() => {
        if (active) setAuth("error");
      });
    return () => {
      active = false;
    };
  }, []);
  const me = useQuery({
    queryKey: ["me", identity],
    queryFn: ({ signal }) => api.me(signal),
    enabled: auth === "ready" && !changing,
    retry: false,
  });
  if (auth !== "ready")
    return (
      <div className="login-page">
        <section className="panel login-panel">
          <span className="brand-icon">
            <Radar />
          </span>
          <h1>Радар вузов</h1>
          <p>
            {auth === "loading"
              ? "Проверяем сессию…"
              : auth === "error"
                ? "Keycloak недоступен. Проверьте адрес сервера авторизации."
                : "Рабочее пространство ИТ Школы Ростелекома"}
          </p>
          {auth === "login" && (
            <Button onClick={() => void login()}>
              Войти через Keycloak <ArrowRight size={16} />
            </Button>
          )}
          {auth === "error" && (
            <Button onClick={() => window.location.reload()}>
              Повторить подключение
            </Button>
          )}
        </section>
      </div>
    );
  if (changing || me.isPending)
    return (
      <div className="login-page">
        <Loading />
      </div>
    );
  if (me.isError)
    return (
      <div className="login-page">
        <ErrorState error={me.error} retry={() => void me.refetch()} />
      </div>
    );
  if (!me.data) return null;
  const profile = me.data;
  const allowed = navigation.filter(
    (n) => !n.roles || n.roles.includes(profile.role),
  );
  async function changeIdentity(value: string) {
    setChanging(true);
    await client.cancelQueries();
    client.clear();
    setDevUser(value);
    setIdentity(value);
    setChanging(false);
  }
  return (
    <div className="app">
      <a href="#main" className="skip-link">
        К содержимому
      </a>
      <aside className="sidebar">
        <Link to="/radar" className="brand">
          <span className="brand-icon">
            <Radar size={26} />
          </span>
          <span>
            радар вузов<small>ИТ ШКОЛА РОСТЕЛЕКОМА</small>
          </span>
        </Link>
        <div className="workspace">
          <span className="workspace-icon">Р</span>
          <div>
            <strong>ИТ Школа</strong>
            <small>{profile.team?.name || "Все команды"}</small>
          </div>
        </div>
        <nav>
          {allowed.map((n) => (
            <div key={n.path}>
              {n.section && <div className="nav-label">{n.section}</div>}
              <NavLink
                to={n.path}
                className={({ isActive }) =>
                  isActive ? "nav-link active" : "nav-link"
                }
              >
                <n.icon size={18} />
                {n.title}
              </NavLink>
            </div>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <ShieldCheck size={15} />{" "}
          {mode === "mock"
            ? "Демо по контракту API"
            : "Область данных от сервера"}
          <small>Версия API 0.1.0</small>
        </div>
      </aside>
      <div className="app-body">
        <header className="topbar">
          <div className="breadcrumb">
            Рабочее пространство <ChevronRight size={13} />
            <strong>
              {navigation.find((n) => n.path === location.pathname)?.title ||
                "Карточка"}
            </strong>
          </div>
          <div className="top-actions">
            <span className="demo-badge">
              {mode === "mock"
                ? "MSW · демо"
                : mode === "dev"
                  ? "API · локальный доступ"
                  : "Keycloak"}
            </span>
            {mode !== "keycloak" ? (
              <label>
                <span className="sr-only">Пользователь разработки</span>
                <select
                  aria-label="Пользователь разработки"
                  className="user-select"
                  value={identity}
                  onChange={(e) => void changeIdentity(e.target.value)}
                >
                  {devUsers.map((u) => (
                    <option key={u.email} value={u.email}>
                      {u.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <Button
                variant="ghost"
                onClick={() => {
                  client.clear();
                  setAuth("login");
                  void logout();
                }}
              >
                <LogOut size={15} />
                Выйти
              </Button>
            )}
            <span className="profile-role">{roleNames[profile.role]}</span>
          </div>
        </header>
        <main id="main">
          <Routes>
            <Route path="/" element={<Navigate to="/radar" replace />} />
            <Route
              path="/radar"
              element={<RadarPage key={profile.id} me={profile} />}
            />
            <Route
              path="/interactions"
              element={<InteractionsPage key={profile.id} />}
            />
            <Route
              path="/interactions/:id"
              element={<DetailPage key={profile.id + location.pathname} />}
            />
            <Route
              path="/universities"
              element={<UniversitiesPage key={profile.id} />}
            />
            <Route
              path="/universities/:id"
              element={<UniversityPage key={profile.id + location.pathname} />}
            />
            {Object.keys(planned).map((path) => (
              <Route
                key={path}
                path={path}
                element={
                  allowed.some((n) => n.path === path) ? (
                    <Planned path={path} />
                  ) : (
                    <Empty
                      title="Раздел недоступен"
                      text="Выбранная роль не имеет доступа к этому разделу."
                    />
                  )
                }
              />
            ))}
            <Route path="/help/*" element={<Help />} />
            <Route
              path="*"
              element={
                <Empty
                  title="Страница не найдена"
                  text="Проверьте адрес страницы."
                />
              }
            />
          </Routes>
          <footer>
            Радар вузов<span>Вузы. Программы. Взаимодействия.</span>
            <span>ЛЦТ 2026</span>
          </footer>
        </main>
        <nav className="mobile-nav">
          <NavLink to="/radar">
            <Radar />
            Радар
          </NavLink>
          <NavLink to="/interactions">
            <Layers3 />
            Работа
          </NavLink>
          <NavLink to="/universities">
            <Building2 />
            Вузы
          </NavLink>
          <NavLink to="/help">
            <CircleHelp />
            Справка
          </NavLink>
        </nav>
      </div>
    </div>
  );
}
function Loading() {
  return (
    <div className="panel loading-state" role="status" aria-live="polite">
      <div className="skeleton" />
      <div className="skeleton" />
      <p>Загружаем данные…</p>
    </div>
  );
}
function ErrorState({ error, retry }: { error: Error; retry: () => void }) {
  const e = error instanceof ApiError ? error : null;
  return (
    <section className="panel error-state" role="alert">
      <h2>
        {e?.status === 404
          ? "Запись не найдена или недоступна"
          : e?.status === 401
            ? "Нужна авторизация"
            : "Не удалось получить данные"}
      </h2>
      <p>{cleanCopy(error.message)}</p>
      {e?.code && <code>{e.code}</code>}
      {e?.traceId && <small>Код запроса: {e.traceId}</small>}
      <div>
        <Button variant="outline" onClick={retry}>
          <RefreshCw size={15} />
          Повторить
        </Button>
        {e?.status === 401 && mode === "keycloak" && (
          <Button onClick={() => void login()}>Войти снова</Button>
        )}
      </div>
    </section>
  );
}
function QueryState({ query }: { query: UseQueryResult<unknown, Error> }) {
  return query.isError ? (
    <ErrorState error={query.error} retry={() => void query.refetch()} />
  ) : (
    <Loading />
  );
}
function SearchField({
  value,
  onChange,
  placeholder = "Вуз, программа или продукт",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="search">
      <Search size={16} />
      <input
        type="search"
        aria-label="Поиск"
        maxLength={100}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
function useSearch() {
  const [search, setSearch] = useState("");
  const [value, setValue] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setValue(search.trim()), 250);
    return () => clearTimeout(timer);
  }, [search]);
  return { search, setSearch, value };
}
function Pagination({
  page,
  total,
  onPage,
}: {
  page: number;
  total: number;
  onPage: (p: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / 20));
  return (
    <div className="pagination">
      <span>
        Всего: {total} · Страница {page} из {pages}
      </span>
      <Button
        variant="outline"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
      >
        Назад
      </Button>
      <Button
        variant="outline"
        disabled={page >= pages}
        onClick={() => onPage(page + 1)}
      >
        Далее
      </Button>
    </div>
  );
}
function SignalRow({ signal: s }: { signal: Signal }) {
  const Icon = icons[s.kind];
  return (
    <Link className="signal" to={`/interactions/${s.interaction.id}`}>
      <span className={`signal-icon ${s.kind}`}>
        <Icon size={19} />
      </span>
      <div className="signal-main">
        <div className="signal-title">
          <strong>{s.interaction.university.name}</strong>
          <span className={`badge ${s.severity}`}>{labels[s.severity]}</span>
        </div>
        <p>
          {s.interaction.program.name} · {s.interaction.product.name}
        </p>
        <div className="signal-reason">{cleanCopy(s.message)}</div>
        <div className="signal-meta">
          <span>{kinds[s.kind]}</span>
          <span>{s.interaction.owner.full_name}</span>
        </div>
      </div>
      <ChevronRight className="signal-arrow" size={17} />
    </Link>
  );
}
function RadarPage({ me }: { me: Me }) {
  const { search, setSearch, value } = useSearch();
  const [kind, setKind] = useState<Schema["SignalKind"] | "">("");
  const [severity, setSeverity] = useState<Schema["Severity"] | "">("");
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [value, kind, severity]);
  const results = useQuery({
    queryKey: ["signals", value, kind, severity, page],
    queryFn: ({ signal }) =>
      api.signals(
        {
          search: value || undefined,
          kind: kind ? [kind] : undefined,
          severity: severity ? [severity] : undefined,
          page,
          page_size: 20,
        },
        signal,
      ),
  });
  const counts = useQuery({
    queryKey: ["signal-counts"],
    queryFn: async ({ signal }) =>
      Object.fromEntries(
        await Promise.all(
          (Object.keys(kinds) as Schema["SignalKind"][]).map(async (k) => [
            k,
            (await api.signals({ kind: [k], page_size: 1 }, signal)).total,
          ]),
        ),
      ),
  });
  const overview = useQuery({
    queryKey: ["interaction-count"],
    queryFn: ({ signal }) => api.interactions({ page_size: 1 }, signal),
  });
  return (
    <>
      <Heading
        eyebrow={
          mode === "mock"
            ? "ДЕМОНСТРАЦИЯ ПО КОНТРАКТУ API"
            : "РАБОЧЕЕ ПРОСТРАНСТВО"
        }
        title={me.role === "kam" ? "Всё важное на радаре" : "Радар команды"}
        text={`${me.full_name}, здесь собраны сигналы в вашей области доступа.`}
      >
        <Button asChild variant="outline">
          <Link to="/interactions">
            Взаимодействия <ArrowUpRight size={16} />
          </Link>
        </Button>
      </Heading>
      <div className="crm-intro">
        <div>
          <span className="eyebrow">В ФОКУСЕ</span>
          <h2>От контакта к результату</h2>
          <p>
            Контролируйте этапы, сроки лицензий и документы в одном
            пространстве.
          </p>
        </div>
        <div className="intro-total">
          <strong>{overview.data?.total ?? "…"}</strong>
          <span>взаимодействий</span>
        </div>
      </div>
      {counts.isError ? (
        <ErrorState error={counts.error} retry={() => void counts.refetch()} />
      ) : (
        <section className="metric-grid">
          {(Object.keys(kinds) as Schema["SignalKind"][]).map((k, n) => {
            const Icon = icons[k];
            return (
              <button
                key={k}
                className={`metric-card metric-${n} ${kind === k ? "selected" : ""}`}
                aria-pressed={kind === k}
                onClick={() => setKind(kind === k ? "" : k)}
              >
                <div className="metric-top">
                  <span className="metric-icon">
                    <Icon size={20} />
                  </span>
                  <ArrowUpRight size={14} />
                </div>
                <div className="metric-value">{counts.data?.[k] ?? "…"}</div>
                <strong>{kinds[k]}</strong>
              </button>
            );
          })}
        </section>
      )}
      <section className="panel">
        <div className="section-heading">
          <div>
            <h2>Требуют внимания</h2>
            <p>Каждый сигнал содержит объяснение от сервера</p>
          </div>
          <Button
            variant="ghost"
            aria-label="Обновить радар"
            onClick={() => {
              void results.refetch();
              void counts.refetch();
              void overview.refetch();
            }}
          >
            <RefreshCw size={17} />
          </Button>
        </div>
        <div className="filters">
          <SearchField value={search} onChange={setSearch} />
          <select
            aria-label="Важность"
            value={severity}
            onChange={(e) => setSeverity(e.target.value as typeof severity)}
          >
            <option value="">Все приоритеты</option>
            {Object.entries(labels).map(([id, label]) => (
              <option key={id} value={id}>
                {label}
              </option>
            ))}
          </select>
          {kind && (
            <Button variant="ghost" onClick={() => setKind("")}>
              Все сигналы <X size={14} />
            </Button>
          )}
        </div>
        {!results.data ? (
          <QueryState query={results} />
        ) : results.isError ? (
          <ErrorState
            error={results.error}
            retry={() => void results.refetch()}
          />
        ) : (
          <>
            {results.data.items.map((s) => (
              <SignalRow key={s.id} signal={s} />
            ))}
            {!results.data.items.length && (
              <Empty
                title="Сигналов нет"
                text="Измените фильтры или продолжайте работу с взаимодействиями."
              />
            )}
            <Pagination
              page={page}
              total={results.data.total}
              onPage={setPage}
            />
          </>
        )}
      </section>
    </>
  );
}
function InteractionRows({
  items,
}: {
  items: Schema["InteractionListItem"][];
}) {
  return (
    <>
      {items.map((i) => (
        <Link
          className="interaction-card"
          to={`/interactions/${i.id}`}
          key={i.id}
        >
          <span className="university-icon">
            <Building2 size={21} />
          </span>
          <div>
            <strong>{i.university.name}</strong>
            <p>
              {i.program.name} · {i.product.name}
            </p>
            <small>
              {i.owner.full_name} · Сигналов: {i.open_signals.length}
            </small>
          </div>
          <div className="stage-tag">
            {i.stage.name}
            <small>{i.days_on_stage} дн. на этапе</small>
          </div>
          <ChevronRight size={16} />
        </Link>
      ))}
    </>
  );
}
function InteractionsPage({ universityId }: { universityId?: string }) {
  const { search, setSearch, value } = useSearch();
  const [stage, setStage] = useState("");
  const [owner, setOwner] = useState("");
  const [page, setPage] = useState(1);
  const workflow = useQuery({
    queryKey: ["workflow"],
    queryFn: ({ signal }) => api.workflow(signal),
  });
  const users = useQuery({
    queryKey: ["users"],
    queryFn: ({ signal }) => api.users(signal),
  });
  useEffect(() => setPage(1), [value, stage, owner, universityId]);
  const filters: InteractionFilters = {
    search: value || undefined,
    stage_code: stage ? [stage] : undefined,
    owner_id: owner ? [owner] : undefined,
    university_id: universityId ? [universityId] : undefined,
    page,
    page_size: 20,
  };
  const results = useQuery({
    queryKey: ["interactions", filters],
    queryFn: ({ signal }) => api.interactions(filters, signal),
  });
  return (
    <>
      {!universityId && (
        <Heading
          eyebrow="РАБОЧЕЕ ПРОСТРАНСТВО"
          title="Взаимодействия"
          text="Вуз × программа × продукт. Этапы и ответственные из API."
        />
      )}
      <section className="panel">
        <div className="filters">
          <SearchField value={search} onChange={setSearch} />
          <select
            aria-label="Этап"
            value={stage}
            onChange={(e) => setStage(e.target.value)}
            disabled={!workflow.data}
          >
            <option value="">Все этапы</option>
            {workflow.data?.stages.map((s) => (
              <option key={s.id} value={s.code}>
                {s.name}
              </option>
            ))}
          </select>
          <select
            aria-label="Ответственный"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            disabled={!users.data}
          >
            <option value="">Все ответственные</option>
            {users.data?.map((u) => (
              <option key={u.id} value={u.id}>
                {u.full_name}
              </option>
            ))}
          </select>
        </div>
        {workflow.isError && (
          <ErrorState
            error={workflow.error}
            retry={() => void workflow.refetch()}
          />
        )}
        {users.isError && (
          <ErrorState error={users.error} retry={() => void users.refetch()} />
        )}
        {!results.data ? (
          <QueryState query={results} />
        ) : results.isError ? (
          <ErrorState
            error={results.error}
            retry={() => void results.refetch()}
          />
        ) : (
          <>
            <InteractionRows items={results.data.items} />
            {!results.data.items.length && (
              <Empty
                title="Ничего не найдено"
                text="Измените запрос или фильтры."
              />
            )}
            <Pagination
              page={page}
              total={results.data.total}
              onPage={setPage}
            />
          </>
        )}
      </section>
    </>
  );
}
function DetailPage() {
  const { id = "" } = useParams();
  const result = useQuery(interactionQueryOptions(api, id));
  if (!result.data) return <QueryState query={result} />;
  if (result.isError)
    return (
      <ErrorState error={result.error} retry={() => void result.refetch()} />
    );
  return <Detail key={id} card={result.data} />;
}
function Detail({ card }: { card: Card }) {
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const [comment, setComment] = useState("");
  const [targetId, setTargetId] = useState("");
  const [tab, setTab] = useState("История");
  const [success, setSuccess] = useState("");
  const target = card.allowed_transitions.find(
    (t) => t.to_stage.id === targetId,
  );
  const mutation = useMutation({
    mutationFn: () =>
      api.transition(card.id, {
        to_stage_id: targetId,
        comment,
        expected_version: card.version,
        attachment_ids: [],
      }),
    retry: false,
    onSuccess: (result) => {
      client.setQueryData(["interaction", card.id], result.interaction);
      for (const key of [
        "signals",
        "signal-counts",
        "interactions",
        "interaction-count",
        "universities",
        "university",
      ])
        void client.invalidateQueries({ queryKey: [key] });
      setOpen(false);
      setComment("");
      setSuccess("Переход сохранён. История и сигналы обновлены.");
    },
  });
  const conflict =
    mutation.error instanceof ApiError && mutation.error.status === 409;
  return (
    <>
      <Link to="/interactions" className="back-link">
        ← Все взаимодействия
      </Link>
      <Heading
        eyebrow={`ВЕРСИЯ ЗАПИСИ ${card.version}`}
        title={card.university.name}
        text={`${card.program.name} · ${card.product.name}`}
      >
        <Button
          disabled={
            !card.allowed_transitions.length || card.status !== "active"
          }
          onClick={() => {
            setTargetId(card.allowed_transitions[0]?.to_stage.id || "");
            mutation.reset();
            setOpen(true);
          }}
        >
          Изменить этап <ArrowRight size={16} />
        </Button>
      </Heading>
      <div className="detail-grid">
        <section className="panel detail-summary">
          <span className="eyebrow">ТЕКУЩИЙ ЭТАП</span>
          <h2>{card.stage.name}</h2>
          <p>
            {card.days_on_stage} дн. на этапе
            {card.norm_days !== null ? ` · Норма ${card.norm_days} дн.` : ""}
          </p>
          <div className="detail-fields">
            <div>
              <small>Ответственный</small>
              <strong>{card.owner.full_name}</strong>
            </div>
            <div>
              <small>Вуз</small>
              <strong>
                <Link to={`/universities/${card.university.id}`}>
                  {card.university.short_name} <ArrowUpRight size={12} />
                </Link>
              </strong>
            </div>
          </div>
        </section>
        <section className="tip">
          <h3>Сигналы: {card.signals.length}</h3>
          {card.signals.length ? (
            card.signals.map((s) => <p key={s.id}>{cleanCopy(s.message)}</p>)
          ) : (
            <p>Открытых сигналов нет.</p>
          )}
        </section>
      </div>
      <section className="panel">
        <div className="tabs detail-tabs">
          {["История", "Договор", "Документы"].map((t) => (
            <button
              key={t}
              className={tab === t ? "tab active" : "tab"}
              onClick={() => setTab(t)}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="detail-content">
          {tab === "История" ? (
            <>
              <h3>История переходов</h3>
              {card.history.map((h) => (
                <div className="history-item" key={h.id}>
                  <span className="history-dot" />
                  <div>
                    <strong>
                      {h.from_stage?.name || "Начало"} → {h.to_stage.name}
                    </strong>
                    {h.comment && <p>{h.comment}</p>}
                    <small>
                      {date(h.occurred_at)} · {h.actor?.full_name || "Система"}
                    </small>
                  </div>
                </div>
              ))}
              {!card.history.length && <p>Переходов пока нет.</p>}
            </>
          ) : tab === "Договор" ? (
            card.contract ? (
              <>
                <h3>Договор {card.contract.number}</h3>
                <p>
                  Лицензия до:{" "}
                  {card.contract.license_valid_until || "Не указано"}
                </p>
                <p>
                  Статус передачи:{" "}
                  {card.contract.transfer_status || "Не указан"}
                </p>
              </>
            ) : (
              <p>Договор не указан в карточке.</p>
            )
          ) : (
            <>
              <h3>Документы</h3>
              <p>
                Методы загрузки файлов ещё не опубликованы в контракте API. Если
                переход требует документ, он будет недоступен до подключения
                загрузки.
              </p>
            </>
          )}
        </div>
      </section>
      {success && (
        <p role="status" className="success-message">
          {success}
        </p>
      )}
      <Dialog.Root
        open={open}
        onOpenChange={(value) => {
          if (!mutation.isPending) setOpen(value);
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="dialog-overlay" />
          <Dialog.Content className="dialog-content">
            <Dialog.Title>Изменить этап</Dialog.Title>
            <Dialog.Description>
              Выберите переход, разрешённый сервером для текущей версии записи.
            </Dialog.Description>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (
                  target &&
                  !target.requires_attachment &&
                  !conflict &&
                  !mutation.isPending
                )
                  mutation.mutate();
              }}
            >
              <label className="form-label" htmlFor="target">
                Новый этап
              </label>
              <select
                id="target"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                disabled={mutation.isPending}
              >
                <option value="" disabled>
                  Выберите этап
                </option>
                {card.allowed_transitions.map((t) => (
                  <option value={t.to_stage.id} key={t.to_stage.id}>
                    {t.to_stage.name}
                  </option>
                ))}
              </select>
              <label className="form-label" htmlFor="comment">
                Комментарий{target?.requires_comment ? " (обязательно)" : ""}
              </label>
              <textarea
                id="comment"
                required={target?.requires_comment}
                maxLength={4000}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                disabled={mutation.isPending}
                placeholder="Что сделано и о чём договорились?"
              />
              <small>{comment.length} / 4000</small>
              {target?.requires_attachment && (
                <p role="alert" className="form-note">
                  Для этого перехода нужен файл. Загрузка ожидает контракт v1.
                </p>
              )}
              {mutation.isError && (
                <div className="transition-error" role="alert">
                  <p>{cleanCopy(mutation.error.message)}</p>
                  {mutation.error instanceof ApiError && (
                    <>
                      <code>{mutation.error.code}</code>
                      {mutation.error.fields.map((f) => (
                        <p key={f.field}>
                          {f.field}: {cleanCopy(f.message)}
                        </p>
                      ))}
                      {mutation.error.status === 409 && (
                        <Button
                          type="button"
                          variant="outline"
                          onClick={async () => {
                            await client.invalidateQueries({
                              queryKey: ["interaction", card.id],
                            });
                            mutation.reset();
                            setTargetId("");
                          }}
                        >
                          Обновить карточку
                        </Button>
                      )}
                    </>
                  )}
                </div>
              )}
              <div className="dialog-actions">
                <Button
                  type="button"
                  variant="outline"
                  disabled={mutation.isPending}
                  onClick={() => setOpen(false)}
                >
                  Отмена
                </Button>
                <Button
                  type="submit"
                  disabled={
                    conflict ||
                    !target ||
                    target.requires_attachment ||
                    mutation.isPending ||
                    (target.requires_comment && !comment.trim())
                  }
                >
                  {mutation.isPending ? "Сохраняем…" : "Сохранить переход"}
                </Button>
              </div>
            </form>
            <Dialog.Close
              className="dialog-close"
              disabled={mutation.isPending}
              aria-label="Закрыть"
            >
              <X size={20} />
            </Dialog.Close>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
function UniversitiesPage() {
  const { search, setSearch, value } = useSearch();
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [value]);
  const result = useQuery({
    queryKey: ["universities", value, page],
    queryFn: ({ signal }) =>
      api.universities(
        { search: value || undefined, page, page_size: 20 },
        signal,
      ),
  });
  return (
    <>
      <Heading
        eyebrow="КАТАЛОГ"
        title="Вузы"
        text="Счётчики взаимодействий и сигналов из вашей области данных."
      />
      <SearchField
        value={search}
        onChange={setSearch}
        placeholder="Название вуза или регион"
      />
      {!result.data ? (
        <QueryState query={result} />
      ) : result.isError ? (
        <ErrorState error={result.error} retry={() => void result.refetch()} />
      ) : (
        <>
          <div className="university-grid">
            {result.data.items.map((u) => (
              <Link
                to={`/universities/${u.id}`}
                key={u.id}
                className="panel university-card"
              >
                <div className="university-card-top">
                  <span className="university-icon">
                    <Building2 />
                  </span>
                  <ArrowUpRight size={17} />
                </div>
                <small>{u.region}</small>
                <h2>{u.name}</h2>
                <p>Взаимодействий: {u.interactions_count}</p>
                <p>Сигналов: {u.open_signals_count}</p>
              </Link>
            ))}
          </div>
          {!result.data.items.length && (
            <Empty title="Вузы не найдены" text="Измените поисковый запрос." />
          )}
          <Pagination page={page} total={result.data.total} onPage={setPage} />
        </>
      )}
    </>
  );
}
function UniversityPage() {
  const { id = "" } = useParams();
  const result = useQuery({
    queryKey: ["university", id],
    queryFn: ({ signal }) => api.university(id, signal),
  });
  if (!result.data) return <QueryState query={result} />;
  if (result.isError)
    return (
      <ErrorState error={result.error} retry={() => void result.refetch()} />
    );
  return (
    <>
      <Link className="back-link" to="/universities">
        ← Все вузы
      </Link>
      <Heading
        eyebrow={result.data.region}
        title={result.data.name}
        text={`Взаимодействий: ${result.data.interactions_count} · Сигналов: ${result.data.open_signals_count}`}
      />
      <InteractionsPage universityId={id} />
    </>
  );
}
function Help() {
  return (
    <>
      <Heading
        eyebrow="СПРАВКА"
        title="Работа с API v0"
        text="Фронтенд и сервер используют общий контракт."
      />
      <section className="panel help-section">
        <h2>Как проверить взаимодействие</h2>
        <ol>
          <li>Откройте сигнал радара.</li>
          <li>Изучите историю и договор.</li>
          <li>Выберите один из разрешённых переходов.</li>
          <li>Добавьте комментарий и сохраните.</li>
        </ol>
        <p>
          При конфликте версий обновите карточку. Комментарий останется в форме.
          Повторный переход требует вашего подтверждения.
        </p>
        <h3>Текущий режим: {mode}</h3>
        <p>
          {mode === "mock"
            ? "MSW возвращает синтетические ответы по контракту. Изменения хранятся в памяти вкладки и сбрасываются при перезагрузке. Это не живой бэкенд."
            : mode === "dev"
              ? "Запросы уходят в настоящий API с X-Dev-User. Режим разрешён только для локальной разработки."
              : "Вход через Keycloak. API проверяет роль и область данных. Токены хранятся только в памяти."}
        </p>
        <p>
          Загрузка документов, импорт, отчёты, рейтинг и SSE ожидают следующие
          версии API.
        </p>
      </section>
    </>
  );
}
