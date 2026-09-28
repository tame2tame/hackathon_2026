import { expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import type { ReactNode } from "react";
import { Payments } from "./Payments";
import { VendorRow, VendorContacts } from "./Vendors";
import { mockUsers, uid } from "../mocks/fixtures";
const vendor = {
  id: uid(90),
  name: "Тестовый вендор",
  products: [{ id: uid(91), name: "Тестовый продукт" }],
  contacts: 1,
  archived_at: null,
};
function render(node: ReactNode) {
  const client = new QueryClient();
  client.setQueryData(
    ["service", "/counterparty-groups", {}],
    [{ id: uid(31), code: "b2c" }],
  );
  client.setQueryData(["service", "/programs", {}], []);
  client.setQueryData(
    ["service", `/vendors/${vendor.id}/contacts`, {}],
    [
      {
        id: uid(92),
        full_name: "Тестовый Контакт",
        email: "test@example.com",
        phone: null,
        channels: ["telegram"],
        products: vendor.products,
      },
    ],
  );
  const html = renderToStaticMarkup(
    <QueryClientProvider client={client}>
      <MemoryRouter>{node}</MemoryRouter>
    </QueryClientProvider>,
  );
  client.clear();
  return html;
}
it("разрешает импорт оплат руководителю и админу, но не КАМу; выгрузка доступна всем", () => {
  for (const me of mockUsers) {
    const html = render(<Payments me={me} />);
    expect(html.includes("Проверить оплаты")).toBe(me.role !== "kam");
    expect(html).toContain("Скачать пользователей для LMS");
    expect(html).not.toContain("Применить оплаты");
    expect(html).toContain(`group=${uid(31)}&amp;stage=enrollment`);
  }
});
it("свёрнутый вендор не раскрывает закэшированные контакты", () => {
  const html = render(<VendorRow vendor={vendor} me={mockUsers[3]} />);
  expect(html).toContain("Тестовый продукт");
  expect(html).toContain(vendor.id);
  expect(html).not.toContain("test@example.com");
  expect(html).toContain('aria-expanded="false"');
});
it("контакты показывают продукты и каналы; изменение ограничено ролью", () => {
  for (const me of mockUsers) {
    const html = render(<VendorContacts vendor={vendor} me={me} />);
    expect(html).toContain("test@example.com");
    expect(html).toContain("Telegram");
    expect(html).toContain("Тестовый продукт");
    expect(html.includes("Добавить контакт")).toBe(me.role !== "kam");
    expect(html.includes("В архив")).toBe(me.role !== "kam");
  }
});
