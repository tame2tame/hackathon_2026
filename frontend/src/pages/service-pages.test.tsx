import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { ServicePage } from "./ServicePage";
import { mockUsers } from "../mocks/fixtures";
import { Select } from "../components/ui/select";
import { Field } from "./shared";
import { Bars } from "./Analytics";
import { Markdown } from "../components/Markdown";
describe("Рабочие экраны", () => {
  for (const [path, title] of Object.entries({
    "/analytics/rating": "Рейтинг востребованности",
    "/analytics/stats": "Статистика",
    "/reports": "Отчёты",
    "/import": "Импорт данных",
    "/team": "Команда",
    "/admin/workflows": "Этапы взаимодействий",
    "/admin/catalogs": "Каталоги",
    "/admin/access": "Пользователи и доступ",
    "/admin/settings": "Настройки",
    "/admin/integrations": "Интеграции",
    "/admin/audit": "Журнал аудита",
  })) {
    it(`отрисовывает ${path} с загрузкой вместо заглушки`, () => {
      const client = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const html = renderToStaticMarkup(
        <QueryClientProvider client={client}>
          <MemoryRouter>
            <ServicePage path={path} me={mockUsers[3]} />
          </MemoryRouter>
        </QueryClientProvider>,
      );
      expect(html).toContain(title);
      expect(html).not.toContain("Скоро");
      expect(html).not.toContain("undefined");
      client.clear();
    });
  }
  it("связывает заголовок поля с доступным оформленным списком", () => {
    const html = renderToStaticMarkup(
      <Field label="Программа">
        <Select value="one">
          <option value="one">Курс</option>
        </Select>
      </Field>,
    );
    expect(html).toContain('class="select-trigger"');
    expect(html).toContain('aria-label="Программа"');
    expect(html).toContain('aria-haspopup="dialog"');
    expect(html).toContain("Курс");
  });
  it("диаграмма различает интерактивный фильтр и пассивные данные", () => {
    const chart = {
      title: "Этапы",
      labels: ["Подписание"],
      values: [0],
      option: {},
    };
    const interactive = renderToStaticMarkup(
      <Bars chart={chart} onPick={() => {}} />,
    );
    const staticChart = renderToStaticMarkup(<Bars chart={chart} />);
    expect(interactive).not.toContain("disabled");
    expect(staticChart).toContain("disabled");
    expect(interactive).toContain("Нет данных");
  });
  it("справка не исполняет HTML и небезопасные ссылки", () => {
    const html = renderToStaticMarkup(
      <Markdown
        text={
          "# Справка\n<script>alert(1)</script>\n[ссылка](javascript:alert)\n**Документы**"
        }
      />,
    );
    expect(html).not.toContain("<script>");
    expect(html).not.toContain('href="javascript:');
    expect(html).toContain("<strong>Документы</strong>");
  });
});
