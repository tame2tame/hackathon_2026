import { NetworkSculpture } from "./components/NetworkSculpture";
import { useEffect, useRef, useState, type ElementType } from "react";
import {
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useParams,
} from "react-router-dom";
import * as Dialog from "@radix-ui/react-dialog";
import {
  Radar,
  Layers3,
  Building2,
  ChartNoAxesCombined,
  ChartPie,
  FileText,
  Users,
  Upload,
  Workflow,
  BookOpen,
  ArrowUpRight,
  ArrowRight,
  Search,
  SlidersHorizontal,
  Clock3,
  FileWarning,
  CalendarClock,
  CirclePause,
  ChevronRight,
  X,
  LayoutGrid,
  List,
  ShieldCheck,
  Settings2,
  Cable,
  History,
  CircleHelp,
  RotateCcw,
} from "lucide-react";
import { Button } from "./components/ui/button";
import {
  advance,
  hasSignal,
  initialData,
  kinds,
  roleNames,
  stages,
  visibleData,
  type Interaction,
  type Kind,
  type Role,
} from "./lib/data";
const iconKinds = {
  stage_overdue: Clock3,
  license_expiring: CalendarClock,
  missing_document: FileWarning,
  inactivity: CirclePause,
};
export const navigation: {
  path: string;
  title: string;
  icon: ElementType;
  roles?: Role[];
  section?: string;
}[] = [
  {
    path: "/radar",
    title: "Радар",
    icon: Radar,
    section: "РАБОЧЕЕ ПРОСТРАНСТВО",
  },
  { path: "/interactions", title: "Взаимодействия", icon: Layers3 },
  { path: "/universities", title: "Вузы", icon: Building2 },
  {
    path: "/analytics/rating",
    title: "Рейтинг",
    icon: ChartNoAxesCombined,
    section: "АНАЛИТИКА",
  },
  { path: "/analytics/stats", title: "Статистика", icon: ChartPie },
  { path: "/reports", title: "Отчёты", icon: FileText },
  {
    path: "/team",
    title: "Команда",
    icon: Users,
    roles: ["manager", "admin"],
    section: "УПРАВЛЕНИЕ",
  },
  {
    path: "/import",
    title: "Импорт данных",
    icon: Upload,
    roles: ["manager", "admin"],
  },
  {
    path: "/admin/workflows",
    title: "Этапы взаимодействий",
    icon: Workflow,
    roles: ["manager", "admin"],
  },
  {
    path: "/admin/catalogs",
    title: "Каталоги",
    icon: BookOpen,
    roles: ["manager", "admin"],
  },
  {
    path: "/admin/access",
    title: "Пользователи и доступ",
    icon: ShieldCheck,
    roles: ["admin"],
  },
  {
    path: "/admin/integrations",
    title: "Интеграции",
    icon: Cable,
    roles: ["manager", "admin"],
  },
  {
    path: "/admin/settings",
    title: "Настройки",
    icon: Settings2,
    roles: ["admin"],
  },
  { path: "/admin/audit", title: "Аудит", icon: History, roles: ["admin"] },
  { path: "/help", title: "Справка", icon: CircleHelp, section: "ПОМОЩЬ" },
];
export const planned: Record<
  string,
  { text: string; items: string[]; date: string }
> = {
  "/reports": {
    text: "Отчёт по взаимодействиям за выбранный период",
    items: [
      "Период и фильтры: вуз, программа, продукт, ответственный",
      "Выбор колонок и формата: XLS, XLSX, PDF, JSON",
      "Очередь формирования, прогресс и скачивание",
    ],
    date: "20-22.09",
  },
  "/analytics/rating": {
    text: "Какие программы и вузы наиболее востребованы",
    items: [
      "Вклад заявок, обучающихся и потоков в балл 0-100",
      "Веса 40 / 40 / 20 и объяснение каждого балла",
      "Фильтр направления, период и отметки неполных данных",
    ],
    date: "23-24.09",
  },
  "/analytics/stats": {
    text: "Путь от первого контакта до обучения",
    items: [
      "Воронка по 14 этапам",
      "Длительность этапов относительно нормы",
      "Динамика переходов и экспорт графиков в PNG / PDF",
    ],
    date: "23-24.09",
  },
  "/team": {
    text: "Нагрузка команды и распределение ответственности",
    items: [
      "Список КАМов: взаимодействия и сигналы",
      "Назначение и замена ответственного",
      "Групповая передача взаимодействий",
    ],
    date: "20-24.09",
  },
  "/import": {
    text: "Перенесите каталоги из таблиц в рабочее пространство",
    items: [
      "Загрузка XLS / XLSX",
      "Сопоставление колонок и сохранённые профили",
      "Предпросмотр конфликтов → применение → итог",
    ],
    date: "17-19.09",
  },
  "/admin/workflows": {
    text: "Настраиваемый путь взаимодействия с вузом",
    items: [
      "14 базовых этапов и нормы длительности",
      "Правила переходов: комментарии и документы",
      "Версии шаблона и карта переноса взаимодействий",
    ],
    date: "23-24.09",
  },
  "/admin/catalogs": {
    text: "Единые справочники для всей команды",
    items: [
      "Вузы, направления, программы",
      "Вендоры и продукты",
      "Контакты вузов и архивирование",
    ],
    date: "23-24.09",
  },
  "/admin/access": {
    text: "Права пользователей и область видимости данных",
    items: [
      "Пользователи и роли Keycloak",
      "Команды и доступ к вузам",
      "Правила разрешения и запрета",
    ],
    date: "23-24.09",
  },
  "/admin/integrations": {
    text: "Связь с LMS и сайтом ИТ Школы",
    items: [
      "Статус источников и время синхронизации",
      "Журнал запусков и коды ошибок",
      "Сопоставление поступивших заявок",
    ],
    date: "23-24.09",
  },
  "/admin/settings": {
    text: "Параметры радара и аналитики",
    items: [
      "Пороги истечения лицензий: 60 / 30 дней",
      "Порог отсутствия активности: 21 день",
      "Веса рейтинга по умолчанию",
    ],
    date: "23-24.09",
  },
  "/admin/audit": {
    text: "История действий пользователей",
    items: [
      "Фильтры по дате, автору и объекту",
      "Значения до и после изменения",
      "Неизменяемая история на стороне сервера",
    ],
    date: "23-24.09",
  },
};
function loadData() {
  try {
    const saved = JSON.parse(localStorage.getItem("radar-demo-v1") || "null");
    if (
      Array.isArray(saved) &&
      saved.length &&
      saved.every(
        (i) =>
          initialData.some((d) => d.id === i.id) &&
          Number.isInteger(i.stage) &&
          i.stage >= 0 &&
          i.stage < 14 &&
          Array.isArray(i.history),
      )
    )
      // Refresh editorial copy while preserving locally saved demo transitions.
      return (saved as Interaction[]).map((item) => ({
        ...item,
        evidence: initialData.find((fixture) => fixture.id === item.id)!
          .evidence,
      }));
  } catch {
    /* Invalid demo storage falls back to known fixtures. */
  }
  return initialData;
}
export default function App() {
  const [role, setRole] = useState<Role>("kam");
  const [data, setData] = useState<Interaction[]>(loadData);
  const [query, setQuery] = useState("");
  const search = useRef<HTMLInputElement>(null);
  const location = useLocation();
  useEffect(() => {
    try {
      localStorage.setItem("radar-demo-v1", JSON.stringify(data));
    } catch {
      /* Demo remains usable if browser storage is disabled. */
    }
  }, [data]);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        search.current?.focus();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  useEffect(() => setQuery(""), [location.pathname]);
  const scoped = visibleData(data, role);
  const filtered = scoped.filter((i) =>
    `${i.university} ${i.program} ${i.product}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  const allowed = navigation.filter((n) => !n.roles || n.roles.includes(role));
  const title =
    navigation.find((n) => location.pathname === n.path)?.title ||
    "Взаимодействие";
  return (
    <div className="app">
      <a href="#main" className="skip-link">
        К содержимому
      </a>
      <aside className="sidebar">
        <Link to="/radar" className="brand">
          <span className="brand-icon">
            <Radar size={27} />
          </span>
          <span>
            радар вузов<small>ИТ ШКОЛА РОСТЕЛЕКОМА</small>
          </span>
        </Link>
        <div className="workspace">
          <span className="workspace-icon">Р</span>
          <div>
            <strong>ИТ Школа</strong>
            <small>Работа с университетами</small>
          </div>
          <ChevronRight size={15} />
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
                <n.icon size={19} />
                <span>{n.title}</span>
                {n.path === "/radar" && (
                  <b>{scoped.filter(hasSignal).length}</b>
                )}
              </NavLink>
            </div>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="status-dot" /> Фронтенд · 15 сентября
          <small>Версия 0.1 / первый день</small>
        </div>
      </aside>
      <div className="app-body">
        <header className="topbar">
          <div className="breadcrumb">
            Рабочее пространство <ChevronRight size={14} />
            <strong>{title}</strong>
          </div>
          <div className="top-actions">
            <span className="demo-badge">Демо-данные</span>
            <label className="role-picker">
              <span className="sr-only">Демонстрационная роль</span>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
              >
                {Object.entries(roleNames).map(([id, label]) => (
                  <option key={id} value={id}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <span className="avatar">
              {role === "kam" ? "АС" : role === "manager" ? "РК" : "АД"}
            </span>
          </div>
        </header>
        <main id="main">
          <Routes>
            <Route path="/" element={<Navigate to="/radar" replace />} />
            <Route
              path="/radar"
              element={
                <RadarPage
                  data={filtered}
                  all={scoped}
                  role={role}
                  query={query}
                  setQuery={setQuery}
                  searchRef={search}
                />
              }
            />
            <Route
              path="/interactions"
              element={
                <Interactions
                  data={filtered}
                  query={query}
                  setQuery={setQuery}
                />
              }
            />
            <Route
              path="/interactions/:id"
              element={
                <Detail
                  data={scoped}
                  onAdvance={(id, c) => setData((d) => advance(d, id, c))}
                />
              }
            />
            <Route
              path="/universities"
              element={
                <Universities
                  data={filtered}
                  query={query}
                  setQuery={setQuery}
                />
              }
            />
            <Route
              path="/universities/:id"
              element={<University data={scoped} />}
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
                      title="Раздел недоступен для этой роли"
                      text="Выберите разрешённый раздел в меню."
                    />
                  )
                }
              />
            ))}
            <Route
              path="/help/*"
              element={<Help onReset={() => setData(initialData)} />}
            />
            <Route
              path="*"
              element={
                <Empty
                  title="Страница не найдена"
                  text="Проверьте адрес или вернитесь на радар."
                />
              }
            />
          </Routes>
          <footer>
            Радар вузов <span>Создаём связи. Развиваем образование.</span>
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
export function Heading({
  eyebrow,
  title,
  text,
  children,
}: {
  eyebrow: string;
  title: string;
  text: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>
      {children}
    </div>
  );
}
function SearchBox({
  query,
  setQuery,
  inputRef,
}: {
  query: string;
  setQuery: (q: string) => void;
  inputRef?: React.Ref<HTMLInputElement>;
}) {
  return (
    <label className="search">
      <Search size={18} />
      <input
        ref={inputRef}
        aria-label="Поиск по вузу, программе или продукту"
        placeholder="Найти вуз, программу или продукт"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <kbd>⌘ K</kbd>
    </label>
  );
}
function RadarPage({
  data,
  all,
  role,
  query,
  setQuery,
  searchRef,
}: {
  data: Interaction[];
  all: Interaction[];
  role: Role;
  query: string;
  setQuery: (q: string) => void;
  searchRef: React.Ref<HTMLInputElement>;
}) {
  const [kind, setKind] = useState<Kind | "all">("all");
  const [severity, setSeverity] = useState("all");
  const signals = data
    .filter(hasSignal)
    .filter(
      (i) =>
        (kind === "all" || i.kind === kind) &&
        (severity === "all" || i.severity === severity),
    )
    .sort(
      (a, b) =>
        ({ high: 0, medium: 1, low: 2 })[a.severity] -
        { high: 0, medium: 1, low: 2 }[b.severity],
    );
  const total = all.filter(hasSignal);
  return (
    <>
      <Heading
        eyebrow="ВТОРНИК, 15 СЕНТЯБРЯ 2026"
        title={role === "kam" ? "Всё важное на радаре" : "Радар вашей команды"}
        text={
          role === "kam"
            ? "Анна, вот что требует внимания в ваших взаимодействиях."
            : "Общая картина рисков и следующие действия команды."
        }
      >
        <Button asChild variant="outline">
          <Link to="/interactions">
            Все взаимодействия <ArrowUpRight size={17} />
          </Link>
        </Button>
      </Heading>
      <div className="hero glass">
        <div className="hero-copy">
          <span className="hero-tag">
            <span className="status-dot" /> /01 · КОНТРОЛЬ ВЗАИМОДЕЙСТВИЙ
          </span>
          <h2>
            РАДАР
            <br />
            <span className="hero-accent">ВУЗОВ</span>
          </h2>
          <div className="hero-manifest">СВЯЗИ. ДАННЫЕ. РЕЗУЛЬТАТ.</div>
          <p>
            Объединяем вузы, программы и продукты в одном пространстве. Начните
            с того, что важно сегодня.
          </p>
          <Link to="/interactions" className="text-link">
            Перейти к взаимодействиям <ArrowRight size={17} />
          </Link>
        </div>
        <NetworkSculpture />
      </div>
      <section className="metric-grid" aria-label="Сигналы по категориям">
        {(Object.keys(kinds) as Kind[]).map((k, index) => {
          const Icon = iconKinds[k];
          return (
            <button
              key={k}
              className={`metric-card metric-${index} ${kind === k ? "selected" : ""}`}
              onClick={() => setKind(kind === k ? "all" : k)}
              aria-pressed={kind === k}
            >
              <div className="metric-top">
                <span className="metric-icon">
                  <Icon size={20} />
                </span>
                <ArrowUpRight size={16} />
              </div>
              <div className="metric-value">
                {total.filter((i) => i.kind === k).length}
                <span>
                  {k === "license_expiring"
                    ? "в ближайшие 60 дней"
                    : k === "inactivity"
                      ? "от 21 дня"
                      : k === "missing_document"
                        ? "нужны вложения"
                        : "превышена норма"}
                </span>
              </div>
              <strong>{kinds[k]}</strong>
            </button>
          );
        })}
      </section>
      <div className="content-grid">
        <section className="panel signals-panel">
          <div className="section-heading">
            <div>
              <h2>
                Требуют внимания <span className="count">{signals.length}</span>
              </h2>
              <p>У каждого сигнала есть причина и следующий шаг</p>
            </div>
            <Radar size={21} className="muted" />
          </div>
          <div className="filters">
            <SearchBox query={query} setQuery={setQuery} inputRef={searchRef} />
            <label className="select-control">
              <SlidersHorizontal size={16} />
              <select
                aria-label="Важность сигнала"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
              >
                <option value="all">Все приоритеты</option>
                <option value="high">Высокий</option>
                <option value="medium">Средний</option>
                <option value="low">Низкий</option>
              </select>
            </label>
          </div>
          <div className="tabs">
            <button
              className={kind === "all" ? "tab active" : "tab"}
              onClick={() => setKind("all")}
            >
              Все сигналы
            </button>
            {kind !== "all" && (
              <button className="tab active" onClick={() => setKind("all")}>
                {kinds[kind]} <X size={12} />
              </button>
            )}
            <span>Сначала важные</span>
          </div>
          {signals.length ? (
            signals.map((i) => <Signal key={i.id} item={i} />)
          ) : (
            <Empty
              title="Всё спокойно"
              text="По выбранным фильтрам сигналов нет. Попробуйте изменить фильтры."
            />
          )}
        </section>
        <aside className="right-column">
          <section className="panel overview">
            <div className="section-heading">
              <h2>В фокусе</h2>
              <span className="tiny-dot" />
            </div>
            <p>
              {role === "kam"
                ? "Ваши взаимодействия"
                : "Взаимодействия команды"}
            </p>
            <div className="focus-number">
              {all.length}
              <span>активных связок</span>
            </div>
            <div className="segmented-bar">
              {total.map((i) => (
                <span
                  key={i.id}
                  style={{
                    background:
                      i.severity === "high"
                        ? "#FF5012"
                        : i.severity === "medium"
                          ? "#8308E9"
                          : "#9A8EA7",
                  }}
                />
              ))}
            </div>
            <div className="legend">
              <span>
                <i style={{ background: "#FF5012" }} />
                Высокий приоритет
              </span>
              <b>{total.filter((i) => i.severity === "high").length}</b>
            </div>
            <div className="legend">
              <span>
                <i style={{ background: "#8308E9" }} />
                Средний приоритет
              </span>
              <b>{total.filter((i) => i.severity === "medium").length}</b>
            </div>
            <div className="legend">
              <span>
                <i style={{ background: "#9A8EA7" }} />
                Низкий приоритет
              </span>
              <b>{total.filter((i) => i.severity === "low").length}</b>
            </div>
            <Link className="overview-link" to="/universities">
              Открыть вузы <ArrowUpRight size={16} />
            </Link>
          </section>
          <section className="tip">
            <div className="tip-icon">
              <Workflow size={23} />
            </div>
            <h3>Один путь. 14 этапов.</h3>
            <p>
              История сохраняет каждый шаг: от поиска контакта до контроля
              обучения.
            </p>
            <Link to="/help">
              Как устроен процесс <ArrowRight size={15} />
            </Link>
          </section>
          <div className="demo-note">
            <ShieldCheck size={17} />
            <span>
              Синтетические данные.
              <br />
              Срез на 15.09.2026.
            </span>
          </div>
        </aside>
      </div>
    </>
  );
}
function Signal({ item: i }: { item: Interaction }) {
  const Icon = iconKinds[i.kind];
  return (
    <Link to={`/interactions/${i.id}`} className="signal">
      <span className={`signal-icon ${i.kind}`}>
        <Icon size={20} />
      </span>
      <div className="signal-main">
        <div className="signal-title">
          <strong>{i.university}</strong>
          <span className={`badge ${i.severity}`}>
            {i.severity === "high"
              ? "Высокий"
              : i.severity === "medium"
                ? "Средний"
                : "Низкий"}
          </span>
        </div>
        <p>
          {i.program}
          <span>·</span>
          {i.product}
        </p>
        <div className="signal-reason">{i.evidence}</div>
        <div className="signal-meta">
          <span>{kinds[i.kind]}</span>
          <span>{i.owner}</span>
        </div>
      </div>
      <ChevronRight className="signal-arrow" size={18} />
    </Link>
  );
}
function Interactions({
  data,
  query,
  setQuery,
}: {
  data: Interaction[];
  query: string;
  setQuery: (q: string) => void;
}) {
  const [view, setView] = useState("list");
  const [stage, setStage] = useState("all");
  const items = data.filter(
    (i) => stage === "all" || i.stage === Number(stage),
  );
  return (
    <>
      <Heading
        eyebrow="РАБОЧЕЕ ПРОСТРАНСТВО"
        title="Взаимодействия"
        text="Вуз × ИТ-программа × ИТ-продукт. Весь путь в одной карточке."
      />
      <div className="panel">
        <div className="filters">
          <SearchBox query={query} setQuery={setQuery} />
          <select
            aria-label="Этап"
            value={stage}
            onChange={(e) => setStage(e.target.value)}
          >
            <option value="all">Все этапы</option>
            {stages.map((s, i) => (
              <option key={s} value={i}>
                {s}
              </option>
            ))}
          </select>
          <div className="view-switch">
            <Button
              aria-label="Список"
              variant={view === "list" ? "default" : "ghost"}
              onClick={() => setView("list")}
            >
              <List size={17} />
            </Button>
            <Button
              aria-label="Карточки"
              variant={view === "cards" ? "default" : "ghost"}
              onClick={() => setView("cards")}
            >
              <LayoutGrid size={17} />
            </Button>
          </div>
        </div>
        <div className={view === "cards" ? "cards-grid" : "interaction-list"}>
          {items.map((i) => (
            <Link
              className="interaction-card"
              to={`/interactions/${i.id}`}
              key={i.id}
            >
              <span className="university-icon">
                <Building2 size={22} />
              </span>
              <div>
                <strong>{i.university}</strong>
                <p>
                  {i.program} · {i.product}
                </p>
                <small>{i.owner}</small>
              </div>
              <div className="stage-tag">
                {stages[i.stage]}
                <small>{i.days} дн. на этапе</small>
              </div>
              <ChevronRight size={17} />
            </Link>
          ))}
        </div>
        {!items.length && (
          <Empty
            title="Ничего не найдено"
            text="Измените поисковый запрос или этап."
          />
        )}
      </div>
    </>
  );
}
function Detail({
  data,
  onAdvance,
}: {
  data: Interaction[];
  onAdvance: (id: string, comment: string) => void;
}) {
  const { id } = useParams();
  const item = data.find((i) => i.id === id);
  const [open, setOpen] = useState(false);
  const [comment, setComment] = useState("");
  const [tab, setTab] = useState("История");
  const [message, setMessage] = useState("");
  if (!item)
    return (
      <Empty
        title="Взаимодействие недоступно"
        text="Запись не найдена или не входит в область видимости выбранной роли."
      />
    );
  return (
    <>
      <Link className="back-link" to="/interactions">
        ← Все взаимодействия
      </Link>
      <Heading
        eyebrow={item.id.toUpperCase()}
        title={item.university}
        text={`${item.program} · ${item.product}`}
      >
        <Button disabled={item.stage === 13} onClick={() => setOpen(true)}>
          Следующий этап <ArrowRight size={17} />
        </Button>
      </Heading>
      <div className="detail-grid">
        <section className="panel detail-summary">
          <span className="eyebrow">ТЕКУЩИЙ ЭТАП · {item.stage + 1} / 14</span>
          <h2>{stages[item.stage]}</h2>
          <p>{item.days} дней на этапе</p>
          <div className="progress-track">
            {stages.map((s, n) => (
              <span
                title={s}
                key={s}
                className={n <= item.stage ? "done" : ""}
              />
            ))}
          </div>
          <div className="detail-fields">
            <div>
              <small>Ответственный</small>
              <strong>{item.owner}</strong>
            </div>
            <div>
              <small>Регион</small>
              <strong>{item.region}</strong>
            </div>
          </div>
        </section>
        <section className="tip">
          <h3>{hasSignal(item) ? kinds[item.kind] : "Этап обновлён"}</h3>
          <p>
            {hasSignal(item)
              ? item.evidence
              : "Сигнал о превышении нормы предыдущего этапа закрыт в демо."}
          </p>
          <span className="badge medium">Демонстрационный сценарий</span>
        </section>
      </div>
      <section className="panel">
        <div className="tabs detail-tabs">
          {["История", "Документы", "Этапы"].map((t) => (
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
              <h3>История взаимодействия</h3>
              {item.history.length ? (
                item.history.map((h, n) => (
                  <div className="history-item" key={n}>
                    <span className="history-dot" />
                    <div>
                      <strong>{h.text}</strong>
                      <p>{h.date} · локальное демо</p>
                    </div>
                  </div>
                ))
              ) : (
                <p>
                  Новых переходов пока нет. Переведите взаимодействие на
                  следующий этап, чтобы проверить сценарий.
                </p>
              )}
            </>
          ) : tab === "Документы" ? (
            <>
              <h3>Документы по этапам</h3>
              <p>
                Загрузка и хранение вложений запланированы на 17-19.09. Для
                подписания потребуется договор, для передачи материалов нужен
                акт, для обучения нужно подтверждение.
              </p>
            </>
          ) : (
            <ol className="stage-list">
              {stages.map((s, n) => (
                <li key={s} className={n === item.stage ? "current" : ""}>
                  {s}
                  {n === item.stage && (
                    <span className="badge medium">Текущий</span>
                  )}
                </li>
              ))}
            </ol>
          )}
        </div>
      </section>
      {message && (
        <p role="status" className="success-message">
          {message}
        </p>
      )}
      <Dialog.Root open={open} onOpenChange={setOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="dialog-overlay" />
          <Dialog.Content className="dialog-content">
            <Dialog.Title>Перевести на следующий этап</Dialog.Title>
            <Dialog.Description>
              {stages[item.stage]} → {stages[item.stage + 1]}
            </Dialog.Description>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                onAdvance(item.id, comment);
                setOpen(false);
                setComment("");
                setMessage(
                  "Переход сохранён в этом браузере. История обновлена.",
                );
              }}
            >
              <label className="form-label" htmlFor="comment">
                Комментарий <span>обязательно</span>
              </label>
              <textarea
                id="comment"
                autoFocus
                required
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Что сделано и о чём договорились?"
              />
              <p className="form-note">
                Демо: комментарий и этап сохраняются локально. Серверная
                проверка документов появится с подключением API.
              </p>
              <div className="dialog-actions">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setOpen(false)}
                >
                  Отмена
                </Button>
                <Button type="submit" disabled={!comment.trim()}>
                  Сохранить переход
                </Button>
              </div>
            </form>
            <Dialog.Close className="dialog-close" aria-label="Закрыть">
              <X size={20} />
            </Dialog.Close>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
function Universities({
  data,
  query,
  setQuery,
}: {
  data: Interaction[];
  query: string;
  setQuery: (q: string) => void;
}) {
  return (
    <>
      <Heading
        eyebrow="КАТАЛОГ"
        title="Вузы"
        text="Университеты, с которыми вы развиваете ИТ-образование."
      />
      <SearchBox query={query} setQuery={setQuery} />
      <div className="university-grid">
        {data.map((i) => (
          <Link
            to={`/universities/${i.id}`}
            className="panel university-card"
            key={i.id}
          >
            <div className="university-card-top">
              <span className="university-icon">
                <Building2 />
              </span>
              <ArrowUpRight size={19} />
            </div>
            <small>{i.region}</small>
            <h2>{i.university}</h2>
            <p>1 взаимодействие · {hasSignal(i) ? 1 : 0} сигнал</p>
            <span className="text-link">
              Открыть обзор <ArrowRight size={16} />
            </span>
          </Link>
        ))}
      </div>
      {!data.length && (
        <Empty title="Вузы не найдены" text="Измените поисковый запрос." />
      )}
    </>
  );
}
function University({ data }: { data: Interaction[] }) {
  const { id } = useParams();
  const i = data.find((x) => x.id === id);
  return i ? (
    <>
      <Link to="/universities" className="back-link">
        ← Все вузы
      </Link>
      <Heading
        eyebrow={i.region}
        title={i.university}
        text="Обзор связок программ и продуктов"
      />
      <section className="panel">
        <Signal item={i} />
      </section>
    </>
  ) : (
    <Empty title="Вуз недоступен" text="Проверьте адрес и выбранную роль." />
  );
}
export function Planned({ path }: { path: string }) {
  const p = planned[path];
  const n = navigation.find((n) => n.path === path)!;
  return (
    <>
      <Heading eyebrow="КАРТА ПРОДУКТА" title={n.title} text={p.text} />
      <section className="panel planned">
        <span className="planned-icon">
          <n.icon size={34} />
        </span>
        <span className="badge medium">Запланировано · {p.date}</span>
        <h2>Структура раздела готова</h2>
        <p>
          На 15.09 подготовлены навигация и место экрана в продукте.
          <br />
          Функции этого раздела появятся на следующем этапе разработки.
        </p>
        <div className="planned-steps">
          {p.items.map((s, i) => (
            <div key={s}>
              <span>0{i + 1}</span>
              <strong>{s}</strong>
            </div>
          ))}
        </div>
        <Button asChild variant="outline">
          <Link to="/radar">
            Вернуться к радару <ArrowRight size={16} />
          </Link>
        </Button>
      </section>
    </>
  );
}
function Help({ onReset }: { onReset: () => void }) {
  const [reset, setReset] = useState(false);
  return (
    <>
      <Heading
        eyebrow="ПОМОЩЬ"
        title="Знакомство с радаром"
        text="Базовый фронтенд · результат первого дня, 15.09.2026"
      />
      <div className="help-grid">
        <section className="panel help-section">
          <h2>Проверьте основной сценарий</h2>
          <ol>
            <li>Откройте сигнал на радаре.</li>
            <li>Изучите причину и текущий этап.</li>
            <li>Нажмите «Следующий этап», добавьте комментарий.</li>
            <li>Проверьте историю и вернитесь на радар.</li>
          </ol>
          <p>
            Для демонстрации видимости меню выберите роль в верхней панели. КАМ
            видит записи Анны, руководитель и администратор видят всю
            демо-команду.
          </p>
          <Button
            variant="outline"
            onClick={() => {
              onReset();
              setReset(true);
            }}
          >
            <RotateCcw size={16} />
            Восстановить демо-данные
          </Button>
          {reset && <p role="status">Начальные данные восстановлены.</p>}
        </section>
        <section className="panel help-section">
          <h2>Что подключим дальше</h2>
          <p>
            Keycloak и настоящие права доступа, API, MSW-моки по общему
            контракту, канбан и документы, импорт, отчёты, рейтинг и статистику.
          </p>
          <p>
            Переключатель ролей показывает поведение интерфейса и не заменяет
            авторизацию. Данные сохраняются только в текущем браузере.
          </p>
          <h3>Основа интерфейса</h3>
          <p>
            React · TypeScript · Vite · Tailwind CSS · Radix UI ·
            shadcn-совместимые компоненты · TanStack Query.
          </p>
        </section>
      </div>
    </>
  );
}
export function Empty({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty">
      <Radar size={30} />
      <h2>{title}</h2>
      <p>{text}</p>
      <Link to="/radar" className="text-link">
        На радар <ArrowRight size={16} />
      </Link>
    </div>
  );
}
