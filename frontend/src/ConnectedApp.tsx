import { BulkActions, Kanban } from "./pages/BulkActions";
import { ClientsPage, Contacts } from "./pages/Clients";
import { SavedViews } from "./pages/SavedViews";
import { useResource } from "./pages/shared";
import {
  LiveUpdates,
  MessagesPage,
  NotificationsPage,
  HelpPage,
} from "./pages/Communication";
import { CreateRecord } from "./pages/CreateRecord";
import { Documents, RecordTools } from "./pages/RecordTools";
import { Select } from "./components/ui/select";

import { RadarCharts } from "./pages/RadarCharts";
import { Menu } from "lucide-react";
import { lazy, Suspense, useEffect, useRef, useState } from "react";
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
  UserRound,
  CheckCircle2,
  ArrowLeft,
} from "lucide-react";
import { navigation, planned, Heading, Empty } from "./App";
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
import { useListControls } from "./lib/use-list-controls";
import { listReturnTo, pageRange, recordStatus } from "./lib/list-state";
import { mode } from "./auth/config";
import {
  currentDevUser,
  setDevUser,
  devUsers,
  initializeSession,
  login,
  logout,
} from "./auth/session";
const ServicePage = lazy(() =>
  import("./pages/ServicePage").then((module) => ({
    default: module.ServicePage,
  })),
);
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
  const [menuOpen, setMenuOpen] = useState(false);
  const [changing, setChanging] = useState(false);
  const client = useQueryClient();
  const location = useLocation();
  useEffect(() => {
    setMenuOpen(false);
    const name =
      navigation.find((n) => n.path === location.pathname)?.title || "Карточка";
    document.title = `${name} · Радар вузов`;
  }, [location.pathname]);
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
        <nav aria-label="Главная навигация">
          <div className="nav-label">РАБОЧЕЕ ПРОСТРАНСТВО</div>
          {allowed.map((n) => (
            <NavLink
              key={n.path}
              to={n.path}
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              <n.icon size={18} />
              <span>{n.title}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <ShieldCheck size={15} />{" "}
          {mode === "mock" ? "Демонстрационный режим" : "Доступ по вашей роли"}
          <small>
            {profile.full_name} · {roleNames[profile.role]}
          </small>
        </div>
      </aside>
      <div className="app-body">
        <header className="topbar">
          <Dialog.Root open={menuOpen} onOpenChange={setMenuOpen}>
            <Dialog.Trigger
              className="mobile-menu-trigger"
              aria-label="Открыть меню"
            >
              <Menu size={22} />
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="dialog-overlay" />
              <Dialog.Content
                className="mobile-drawer"
                aria-describedby={undefined}
              >
                <Dialog.Title>Рабочее пространство</Dialog.Title>
                <Dialog.Close
                  className="dialog-close"
                  aria-label="Закрыть меню"
                >
                  <X />
                </Dialog.Close>
                <nav aria-label="Все разделы">
                  {allowed.map((n) => (
                    <NavLink
                      key={n.path}
                      to={n.path}
                      onClick={() => setMenuOpen(false)}
                    >
                      <n.icon size={20} />
                      {n.title}
                    </NavLink>
                  ))}
                </nav>
                <p>
                  {profile.full_name} · {roleNames[profile.role]}
                </p>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
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
                ? "Демо"
                : mode === "dev"
                  ? "Локальный режим"
                  : "Рабочий режим"}
            </span>
            {mode !== "keycloak" ? (
              <label>
                <span className="sr-only">Пользователь разработки</span>
                <Select
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
                </Select>
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
            <span className="profile-avatar" aria-hidden="true">
              {profile.full_name
                .split(" ")
                .slice(0, 2)
                .map((part) => part[0])
                .join("")}
            </span>
            <span className="profile-role">{roleNames[profile.role]}</span>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          <LiveUpdates identity={profile.id} />
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
                    <Suspense fallback={<Loading />}>
                      <ServicePage path={path} me={profile} />
                    </Suspense>
                  ) : (
                    <Empty
                      title="Раздел недоступен"
                      text="Выбранная роль не имеет доступа к этому разделу."
                    />
                  )
                }
              />
            ))}
            <Route path="/help/*" element={<HelpPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/messages" element={<MessagesPage me={profile} />} />
            <Route path="/notifications" element={<NotificationsPage />} />
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
  placeholder = "Контрагент, программа или продукт",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if (
        (event.metaKey || event.ctrlKey) &&
        event.key.toLowerCase() === "k" &&
        !document.querySelector('[role="dialog"]')
      ) {
        event.preventDefault();
        input.current?.focus();
        input.current?.select();
      }
    };
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, []);
  return (
    <div className="search">
      <Search size={18} aria-hidden="true" />
      <input
        ref={input}
        type="search"
        aria-label="Поиск"
        aria-keyshortcuts="Control+k Meta+k"
        maxLength={100}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Escape") onChange("");
        }}
      />
      {value ? (
        <button
          className="search-clear"
          aria-label="Очистить поиск"
          onClick={() => {
            onChange("");
            input.current?.focus();
          }}
        >
          <X size={16} />
        </button>
      ) : (
        <kbd aria-hidden="true">⌘ / Ctrl K</kbd>
      )}
    </div>
  );
}
function FilterSummary({
  filtered,
  reset,
  total,
  fetching,
}: {
  filtered: boolean;
  reset: () => void;
  total?: number;
  fetching: boolean;
}) {
  return (
    <div className="filter-summary">
      <span role="status" aria-live="polite">
        {fetching
          ? "Обновляем список…"
          : total === undefined
            ? ""
            : `Найдено: ${total}`}
      </span>
      {filtered && (
        <button onClick={reset}>
          <X size={14} /> Сбросить фильтры
        </button>
      )}
    </div>
  );
}
function ListEmpty({
  filtered,
  reset,
  title = "Пока ничего нет",
}: {
  filtered: boolean;
  reset: () => void;
  title?: string;
}) {
  return (
    <div className="list-empty">
      {filtered ? <Search size={28} /> : <CheckCircle2 size={28} />}
      <h3>{filtered ? "Нет совпадений" : title}</h3>
      <p>
        {filtered
          ? "Попробуйте другой запрос или уберите часть фильтров."
          : "Здесь появятся записи, когда они будут доступны."}
      </p>
      {filtered && (
        <Button variant="outline" onClick={reset}>
          Сбросить фильтры
        </Button>
      )}
    </div>
  );
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
        {pageRange(page, total)} · Страница {page} из {pages}
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
export function SignalRow({ signal: s }: { signal: Signal }) {
  const Icon = icons[s.kind];
  const location = useLocation();
  return (
    <Link
      className="signal"
      data-severity={s.severity}
      state={{ returnTo: location.pathname + location.search }}
      to={`/interactions/${s.interaction.id}`}
    >
      <span className={`signal-icon ${s.kind}`}>
        <Icon size={19} />
      </span>
      <div className="signal-main">
        <div className="signal-title">
          <strong>{s.interaction.counterparty.short_name}</strong>
          <span className={`badge ${s.severity}`}>{labels[s.severity]}</span>
        </div>
        <p>
          {s.interaction.program.name} ·{" "}
          {s.interaction.product?.name || "Без продукта"}
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
function GroupSelect({
  value,
  onChange,
  groups,
}: {
  value: string;
  onChange: (value: string) => void;
  groups: UseQueryResult<Schema["CounterpartyGroupOut"][], Error>;
}) {
  return (
    <div className="group-filter">
      <label htmlFor="counterparty-group">Группа контрагентов</label>
      <Select
        id="counterparty-group"
        aria-label="Группа контрагентов"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={!groups.data}
      >
        <option value="">Все группы</option>
        {groups.data?.map((g) => (
          <option key={g.id} value={g.id}>
            {g.name}
          </option>
        ))}
      </Select>
      {groups.isError && (
        <span role="alert">
          Не удалось загрузить группы.{" "}
          <button onClick={() => void groups.refetch()}>Повторить</button>
        </span>
      )}
    </div>
  );
}
function useGroups() {
  return useQuery({
    queryKey: ["groups"],
    queryFn: ({ signal }) => api.groups(signal),
  });
}
function RadarPage({ me }: { me: Me }) {
  const controls = useListControls();
  const {
    group,
    setGroup,
    search,
    setSearch,
    value,
    kind,
    setKind,
    severity,
    setSeverity,
    page,
    setPage,
  } = controls;
  const groups = useGroups();
  const groupFilter = group ? [group] : undefined;
  const results = useQuery({
    queryKey: ["signals", value, kind, severity, group, page],
    queryFn: ({ signal }) =>
      api.signals(
        {
          search: value || undefined,
          group_id: groupFilter,
          kind: kind ? [kind] : undefined,
          severity: severity ? [severity] : undefined,
          page,
          page_size: 20,
        },
        signal,
      ),
  });
  const counts = useQuery({
    queryKey: ["signal-counts", group],
    queryFn: async ({ signal }) =>
      Object.fromEntries(
        await Promise.all(
          (Object.keys(kinds) as Schema["SignalKind"][]).map(async (k) => [
            k,
            (
              await api.signals(
                { kind: [k], page_size: 1, group_id: groupFilter },
                signal,
              )
            ).total,
          ]),
        ),
      ),
  });
  const overview = useQuery({
    queryKey: ["interaction-count", group],
    queryFn: ({ signal }) =>
      api.interactions({ page_size: 1, group_id: groupFilter }, signal),
  });
  return (
    <>
      <Heading
        eyebrow="ОБЗОР РАБОТЫ"
        title={me.role === "kam" ? "Ваш радар" : "Радар команды"}
        text="Замечайте важное вовремя. Выберите сигнал и продолжите работу с записью."
      >
        <Button asChild variant="outline">
          <Link to="/interactions">
            Взаимодействия <ArrowUpRight size={16} />
          </Link>
        </Button>
      </Heading>
      <div className="radar-toolbar">
        <GroupSelect value={group} onChange={setGroup} groups={groups} />
        <div className="overview-inline">
          <Layers3 size={16} />
          {overview.isError ? (
            <button onClick={() => void overview.refetch()}>
              Повторить загрузку счётчика
            </button>
          ) : (
            <span>
              <strong>{overview.data?.total ?? "…"}</strong> взаимодействий в
              выбранных группах
            </span>
          )}
        </div>
      </div>
      {counts.isError ? (
        <ErrorState error={counts.error} retry={() => void counts.refetch()} />
      ) : (
        <section className="metric-grid">
          {(Object.keys(kinds) as Schema["SignalKind"][]).map((k) => {
            const Icon = icons[k];
            return (
              <button
                key={k}
                className={`metric-card ${kind === k ? "selected" : ""}`}
                data-kind={k}
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
      <RadarCharts group={group} />
      <SavedViews page="radar" />
      <section className="panel">
        <div className="section-heading">
          <div>
            <h2>
              Требуют внимания{" "}
              <span className="count-pill">{results.data?.total ?? "…"}</span>
            </h2>
            <p>Причина, срок и ответственный по каждому сигналу</p>
          </div>
          <Button
            variant="ghost"
            aria-label="Обновить радар"
            disabled={results.isFetching || counts.isFetching}
            className={results.isFetching ? "refreshing" : ""}
            onClick={() => {
              void results.refetch();
              void counts.refetch();
              void overview.refetch();
            }}
          >
            <RefreshCw size={17} /> Обновить
          </Button>
        </div>
        <div className="filters">
          <SearchField value={search} onChange={setSearch} />
          <Select
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
          </Select>
          {kind && (
            <button className="filter-chip" onClick={() => setKind("")}>
              {kinds[kind]} <X size={14} />
            </button>
          )}
        </div>
        <FilterSummary
          filtered={controls.filtered}
          reset={controls.reset}
          total={results.data?.total}
          fetching={results.isFetching}
        />
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
              <ListEmpty
                filtered={controls.filtered}
                reset={controls.reset}
                title="Всё под контролем: открытых сигналов нет"
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
export function InteractionRows({
  items,
}: {
  items: Schema["InteractionListItem"][];
}) {
  const location = useLocation();
  return (
    <>
      {items.map((i) => (
        <Link
          className="interaction-card"
          state={{ returnTo: location.pathname + location.search }}
          to={`/interactions/${i.id}`}
          key={i.id}
        >
          <span className="university-icon">
            {i.counterparty.kind === "person" ? (
              <UserRound size={21} />
            ) : (
              <Building2 size={21} />
            )}
          </span>
          <div>
            <strong>{i.counterparty.short_name}</strong>
            <p>
              {i.program.name} · {i.product?.name || "Без продукта"}
            </p>
            <small>
              {i.owner.full_name}{" "}
              <span className={`record-status status-${i.status}`}>
                {recordStatus[i.status] || "Состояние не указано"}
              </span>
              {i.open_signals.length > 0 && (
                <span className="record-signal-count">
                  {i.open_signals.length} сигналов
                </span>
              )}
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
  const controls = useListControls();
  const [view, setView] = useState("list");
  const {
    group,
    setGroup,
    search,
    setSearch,
    value,
    stage,
    setStage,
    direction,
    setDirection,
    owner,
    setOwner,
    page,
    setPage,
  } = controls;
  const groups = useGroups();
  const templateId = groups.data?.find(
    (g) => g.id === group,
  )?.workflow_template_id;
  const workflow = useQuery({
    queryKey: ["workflow", universityId ? "default" : templateId],
    queryFn: ({ signal }) =>
      universityId
        ? api.workflow(signal)
        : api.workflowByTemplate(templateId!, signal),
    enabled: Boolean(universityId || templateId),
  });
  const users = useQuery({
    queryKey: ["users"],
    queryFn: ({ signal }) => api.users(signal),
  });
  const directions = useResource<Schema["DirectionRef"][]>("/directions");
  const filters: InteractionFilters = {
    direction_id: direction ? [direction] : undefined,
    group_id: group ? [group] : undefined,
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
          text="Вузы и клиенты, программы и этапы совместной работы."
        >
          <CreateRecord />
        </Heading>
      )}
      {!universityId && (
        <GroupSelect value={group} onChange={setGroup} groups={groups} />
      )}
      <SavedViews page="interactions" />
      <section className="panel">
        <div className="section-heading">
          <div>
            <h2>Все взаимодействия</h2>
            <p>Контрагенты, ответственные и текущие этапы</p>
          </div>
          <div className="service-tabs">
            <button
              className={view === "list" ? "active" : ""}
              onClick={() => setView("list")}
            >
              Список
            </button>
            <button
              className={view === "board" ? "active" : ""}
              onClick={() => setView("board")}
            >
              Доска
            </button>
          </div>
        </div>
        <div className="filters">
          <SearchField value={search} onChange={setSearch} />
          <Select
            aria-label="Направление"
            value={direction}
            onChange={(e) => setDirection(e.target.value)}
          >
            <option value="">Все направления</option>
            {directions.data?.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Этап"
            value={stage}
            onChange={(e) => setStage(e.target.value)}
            disabled={!workflow.data}
          >
            <option value="">
              {group || universityId ? "Все этапы" : "Сначала выберите группу"}
            </option>
            {workflow.data?.stages.map((s) => (
              <option key={s.id} value={s.code}>
                {s.name}
              </option>
            ))}
          </Select>
          <Select
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
          </Select>
        </div>
        <FilterSummary
          filtered={controls.filtered}
          reset={controls.reset}
          total={results.data?.total}
          fetching={results.isFetching}
        />
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
            <BulkActions items={results.data.items} workflow={workflow.data} />
            {view === "board" ? (
              <>
                <p className="board-note">
                  Доска показывает записи текущей страницы. Откройте карточку
                  для смены этапа.
                </p>
                <Kanban items={results.data.items} />
              </>
            ) : (
              <InteractionRows items={results.data.items} />
            )}
            {!results.data.items.length && (
              <ListEmpty
                filtered={controls.filtered}
                reset={controls.reset}
                title="Взаимодействий пока нет"
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
  const location = useLocation();
  const returnTo = listReturnTo(location.state?.returnTo);
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const [comment, setComment] = useState("");
  const [targetId, setTargetId] = useState("");
  const [attachmentIds, setAttachmentIds] = useState<string[]>([]);
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
        attachment_ids: attachmentIds,
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
      <Link to={returnTo} className="back-link">
        <ArrowLeft size={16} />{" "}
        {returnTo.startsWith("/radar")
          ? "К сигналам радара"
          : "К списку взаимодействий"}
      </Link>
      <Heading
        eyebrow={card.group.name}
        title={card.counterparty.name}
        text={`${card.program.name} · ${card.product?.name || "Без продукта"}`}
      >
        <Button
          disabled={
            !card.allowed_transitions.length || card.status !== "active"
          }
          onClick={() => {
            setTargetId("");
            setAttachmentIds([]);
            mutation.reset();
            setOpen(true);
          }}
        >
          Изменить этап <ArrowRight size={16} />
        </Button>
      </Heading>
      {success && (
        <div className="save-notice" role="status">
          <CheckCircle2 size={20} />
          <span>{success}</span>
          <button
            aria-label="Скрыть уведомление"
            onClick={() => setSuccess("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
      <div className="record-context">
        <span className={`record-status status-${card.status}`}>
          {recordStatus[card.status] || "Состояние не указано"}
        </span>
        <span>Последнее действие: {date(card.last_activity_at)}</span>
      </div>
      {card.status !== "active" && (
        <p className="form-note">
          Смена этапа доступна только у записей в работе.
        </p>
      )}
      <div className="detail-grid">
        <section className="panel detail-summary">
          <span className="eyebrow">ТЕКУЩИЙ ЭТАП</span>
          <h2>{card.stage.name}</h2>
          <div className="stage-timing">
            <div>
              <strong>
                {card.days_on_stage}
                <span> дн.</span>
              </strong>
              <small>На текущем этапе</small>
            </div>
            <div>
              <strong>
                {card.norm_days ?? "—"}
                <span>{card.norm_days !== null ? " дн." : ""}</span>
              </strong>
              <small>
                {card.norm_days !== null ? "Норма этапа" : "Норма не задана"}
              </small>
            </div>
          </div>
          <div className="detail-fields">
            <div>
              <small>Ответственный</small>
              <strong>{card.owner.full_name}</strong>
            </div>
            <div>
              <small>{card.group.name}</small>
              <strong>
                {card.university ? (
                  <Link to={`/universities/${card.university.id}`}>
                    {card.university.short_name} <ArrowUpRight size={12} />
                  </Link>
                ) : (
                  card.counterparty.short_name
                )}
              </strong>
            </div>
          </div>
        </section>
        <section className="panel detail-alerts">
          <h3>
            {card.signals.length
              ? `Требуют внимания · ${card.signals.length}`
              : "Всё под контролем"}
          </h3>
          {card.signals.length ? (
            card.signals.map((s) => {
              const Icon = icons[s.kind];
              return (
                <div
                  className="detail-alert"
                  data-severity={s.severity}
                  key={s.id}
                >
                  <span className={`signal-icon ${s.kind}`}>
                    <Icon size={18} />
                  </span>
                  <div>
                    <strong>{kinds[s.kind]}</strong>
                    <span className={`badge ${s.severity}`}>
                      {labels[s.severity]}
                    </span>
                    <p>{cleanCopy(s.message)}</p>
                  </div>
                </div>
              );
            })
          ) : (
            <p>
              <CheckCircle2 size={20} /> Открытых сигналов нет. Продолжайте
              работу по плану.
            </p>
          )}
        </section>
      </div>
      <section className="panel">
        <div
          className="tabs detail-tabs"
          role="tablist"
          aria-label="Разделы карточки"
        >
          {["История", "Договор", "Документы"].map((t) => (
            <button
              key={t}
              role="tab"
              id={`detail-tab-${t}`}
              aria-selected={tab === t}
              aria-controls="detail-tab-panel"
              tabIndex={tab === t ? 0 : -1}
              onKeyDown={(e) => {
                const names = ["История", "Договор", "Документы"];
                const index = names.indexOf(t);
                const next =
                  e.key === "ArrowRight"
                    ? (index + 1) % 3
                    : e.key === "ArrowLeft"
                      ? (index + 2) % 3
                      : e.key === "Home"
                        ? 0
                        : e.key === "End"
                          ? 2
                          : -1;
                if (next >= 0) {
                  e.preventDefault();
                  setTab(names[next]);
                  document.getElementById(`detail-tab-${names[next]}`)?.focus();
                }
              }}
              className={tab === t ? "tab active" : "tab"}
              onClick={() => setTab(t)}
            >
              {t}
            </button>
          ))}
        </div>
        <div
          className="detail-content"
          id="detail-tab-panel"
          role="tabpanel"
          aria-labelledby={`detail-tab-${tab}`}
          tabIndex={0}
        >
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
              <Documents id={card.id} />
            </>
          )}
        </div>
      </section>

      <RecordTools card={card} />
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
              Выберите доступный этап и опишите причину перехода. Комментарий
              сохранится в истории.
            </Dialog.Description>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (
                  target &&
                  (!target.requires_attachment || attachmentIds.length > 0) &&
                  (!target.requires_comment || !!comment.trim()) &&
                  !conflict &&
                  !mutation.isPending
                )
                  mutation.mutate();
              }}
            >
              <p>
                Сейчас: <strong>{card.stage.name}</strong>
              </p>
              <label className="form-label" htmlFor="target">
                Новый этап
              </label>
              <Select
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
              </Select>
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
                <div className="transition-files">
                  <p>Прикрепите документ. Выбрано: {attachmentIds.length}</p>
                  <Documents
                    id={card.id}
                    onUploaded={(a) =>
                      setAttachmentIds((ids) =>
                        ids.includes(a.id) ? ids : [...ids, a.id],
                      )
                    }
                  />
                </div>
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
                    (target.requires_attachment && !attachmentIds.length) ||
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
  const controls = useListControls();
  const { search, setSearch, value, page, setPage } = controls;
  const location = useLocation();
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
                state={{ returnTo: location.pathname + location.search }}
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
            <ListEmpty
              filtered={controls.filtered}
              reset={controls.reset}
              title="Вузов пока нет"
            />
          )}
          <Pagination page={page} total={result.data.total} onPage={setPage} />
        </>
      )}
    </>
  );
}
function UniversityPage() {
  const location = useLocation();
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
      <Link
        className="back-link"
        to={listReturnTo(location.state?.returnTo, "/universities")}
      >
        ← Все вузы
      </Link>
      <Heading
        eyebrow={result.data.region}
        title={result.data.name}
        text={`Взаимодействий: ${result.data.interactions_count} · Сигналов: ${result.data.open_signals_count}`}
      />
      <Contacts id={id} />
      <InteractionsPage universityId={id} />
    </>
  );
}
