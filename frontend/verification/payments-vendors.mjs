// VITE_AUTH_MODE=dev npm run dev -- --port 5182
// PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node verification/payments-vendors.mjs
// Optional: PLAYWRIGHT_EXECUTABLE=/path/to/chromium, PLAYWRIGHT_BROWSERS_PATH=/path/to/cache
import assert from "node:assert/strict";
const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE || "playwright"
);
const browser = await chromium.launch({
  headless: true,
  ...(process.env.PLAYWRIGHT_EXECUTABLE
    ? { executablePath: process.env.PLAYWRIGHT_EXECUTABLE }
    : {}),
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const base = process.env.FRONTEND_URL || "http://127.0.0.1:5182";
const id = (n) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
let role = "admin",
  contacts = [],
  contactReads = 0;
const imports = [],
  downloads = [],
  creates = [],
  catalogImports = [];
const vendor = {
  id: id(90),
  name: "Тестовый вендор",
  products: [{ id: id(91), name: "Тестовый продукт" }],
  contacts: 0,
  archived_at: null,
};
await page.route("**/api/v1/**", async (route) => {
  const req = route.request(),
    url = new URL(req.url()),
    path = url.pathname.replace("/api/v1", "");
  const json = (data) => route.fulfill({ json: data });
  if (path === "/me")
    return json({
      id: id(4),
      full_name: "Тестовый Администратор",
      email: "test@example.com",
      role,
      scope: "all",
      team: null,
    });
  if (path === "/events")
    return route.fulfill({ contentType: "text/event-stream", body: "" });
  if (path === "/programs")
    return json([
      {
        id: id(80),
        name: "Тестовый курс",
        direction: { id: id(81), name: "Разработка", code: "dev" },
      },
    ]);
  if (path === "/counterparty-groups")
    return json([
      {
        id: id(31),
        code: "b2c",
        name: "Частные лица",
        workflow_template_id: id(32),
      },
    ]);
  if (path === "/vendors") return json([vendor]);
  if (path === `/vendors/${vendor.id}/contacts`) {
    if (req.method() === "GET") {
      contactReads++;
      return json(contacts);
    }
    const body = req.postDataJSON();
    creates.push(body);
    contacts = [
      {
        ...body,
        id: id(92),
        vendor_id: vendor.id,
        products: vendor.products,
        archived_at: null,
      },
    ];
    return json(contacts[0]);
  }
  if (path === `/vendor-contacts/${id(92)}/archive`) {
    contacts = [];
    return json({});
  }
  if (
    path === "/payments/import" ||
    path === "/admin/catalogs/vendor-contacts/import"
  ) {
    const body = req.postData();
    (path === "/payments/import" ? imports : catalogImports).push(body);
    const dry = /name="dry_run"\r\n\r\ntrue/.test(body);
    return json({
      dry_run: dry,
      created: 1,
      updated: 0,
      unchanged: 1,
      errors: 1,
      rows: [
        { row_no: 1, key: "TEST-1", action: "created", detail: null },
        { row_no: 2, key: "TEST-2", action: "error", detail: "Курс не найден" },
        { row_no: 3, key: "TEST-3", action: "unchanged", detail: null },
      ],
    });
  }
  if (path === "/payments/lms-users" || path.includes("/export")) {
    assert.ok(req.headers()["x-dev-user"]);
    downloads.push(url);
    return route.fulfill({
      contentType:
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      body: "test download",
    });
  }
  if (
    ["/clients", "/universities", "/notifications", "/messages"].includes(path)
  )
    return json({ items: [], total: 0, page: 1, page_size: 20 });
  return json([]);
});
try {
  await page.goto(base + "/clients");
  await page
    .getByRole("button", { name: "Проверить оплаты", exact: true })
    .waitFor();
  assert.equal(
    await page
      .getByRole("button", { name: "Применить оплаты", exact: true })
      .count(),
    0,
  );
  await page
    .getByLabel("Файл оплат (JSON, CSV, XLSX, XLS)", { exact: true })
    .setInputFiles({
      name: "payments.json",
      mimeType: "application/json",
      buffer: Buffer.from('[{"Номер заявки":"TEST-1"}]'),
    });
  await page
    .getByRole("button", { name: "Проверить оплаты", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Применить оплаты", exact: true })
    .waitFor();
  assert.match(imports[0], /name="dry_run"\r\n\r\ntrue/);
  assert.ok(
    await page.getByText("Курс не найден", { exact: true }).isVisible(),
  );
  await page
    .getByRole("button", { name: "Кодировка CSV", exact: true })
    .click();
  await page.getByRole("button", { name: "windows-1251", exact: true }).click();
  assert.equal(
    await page
      .getByRole("button", { name: "Применить оплаты", exact: true })
      .count(),
    0,
  );
  await page
    .getByRole("button", { name: "Проверить оплаты", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Применить оплаты", exact: true })
    .click();
  await page.getByText(/Оплаты применены/).waitFor();
  assert.match(imports.at(-1), /name="dry_run"\r\n\r\nfalse/);
  assert.match(imports.at(-1), /windows-1251/);
  await page.getByRole("button", { name: "Курс для LMS", exact: true }).click();
  await page
    .getByRole("button", { name: "Тестовый курс", exact: true })
    .click();
  await page.getByLabel("Номер потока", { exact: true }).fill("3");
  await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Скачать пользователей для LMS" }).click(),
  ]);
  assert.equal(downloads.at(-1).searchParams.get("stream"), "3");
  assert.equal(downloads.at(-1).searchParams.get("program_id"), id(80));
  await page.screenshot({ path: "/tmp/radar-payments.png", fullPage: true });
  await page.goto(base + "/admin/catalogs");
  await page.getByRole("button", { name: "Вендоры", exact: true }).click();
  await page
    .getByRole("button", { name: "Показать контакты", exact: true })
    .waitFor();
  assert.equal(contactReads, 0);
  await page
    .getByRole("button", { name: "Показать контакты", exact: true })
    .click();
  await page
    .getByLabel("ФИО контакта", { exact: true })
    .fill("Тестовый Контакт");
  await page
    .getByLabel("Почта контакта", { exact: true })
    .fill("contact@example.com");
  await page.getByLabel("Telegram", { exact: true }).check();
  await page.getByLabel("Тестовый продукт", { exact: true }).check();
  await page
    .getByRole("button", { name: "Добавить контакт", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Тестовый Контакт", exact: true })
    .waitFor();
  assert.deepEqual(creates[0].channels, ["telegram"]);
  assert.deepEqual(creates[0].product_ids, [id(91)]);
  await page.screenshot({ path: "/tmp/radar-vendors.png", fullPage: true });
  await page
    .getByRole("heading", { name: "Контакты: Тестовый вендор", exact: true })
    .locator("xpath=ancestor::section[1]")
    .getByRole("button", { name: "В архив", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Тестовый Контакт", exact: true })
    .waitFor({ state: "detached" });
  await page
    .getByRole("button", { name: "Контакты вендоров (файл)", exact: true })
    .click();
  await page
    .getByLabel("Файл XLSX, XLS или CSV", { exact: true })
    .setInputFiles({
      name: "contacts.csv",
      mimeType: "text/csv",
      buffer: Buffer.from("Вендор,ФИО\nТестовый вендор,Тестовый Контакт"),
    });
  await page
    .getByRole("button", { name: "Проверить файл", exact: true })
    .click();
  await page.getByRole("button", { name: "Применить", exact: true }).click();
  await page.getByText("Изменения применены", { exact: true }).waitFor();
  assert.match(catalogImports[0], /name="dry_run"\r\n\r\ntrue/);
  assert.match(catalogImports[1], /name="dry_run"\r\n\r\nfalse/);
  await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Выгрузить XLSX" }).click(),
  ]);
  assert.equal(
    downloads.at(-1).pathname,
    "/api/v1/admin/catalogs/vendor-contacts/export",
  );
  role = "kam";
  await page.goto(base + "/clients");
  await page
    .getByRole("button", { name: "Скачать пользователей для LMS" })
    .waitFor();
  assert.equal(
    await page
      .getByRole("button", { name: "Проверить оплаты", exact: true })
      .count(),
    0,
  );
  role = "manager";
  await page.goto(base + "/clients");
  await page
    .getByRole("button", { name: "Проверить оплаты", exact: true })
    .waitFor();
  await page.getByLabel("Номер потока", { exact: true }).fill("0");
  assert.equal(
    await page
      .getByRole("button", { name: "Скачать пользователей для LMS" })
      .count(),
    0,
  );
  await page.route(
    "**/api/v1/payments/import",
    (route) =>
      route.fulfill({
        status: 422,
        json: {
          code: "IMPORT_MAPPING_INVALID",
          detail: "В файле отсутствует курс",
          trace_id: "test-trace",
        },
      }),
    { times: 1 },
  );
  await page
    .getByLabel("Файл оплат (JSON, CSV, XLSX, XLS)", { exact: true })
    .setInputFiles({
      name: "invalid.json",
      mimeType: "application/json",
      buffer: Buffer.from("[]"),
    });
  await page
    .getByRole("button", { name: "Проверить оплаты", exact: true })
    .click();
  await page.getByText("В файле отсутствует курс", { exact: true }).waitFor();
  assert.ok(await page.getByText(/test-trace/).isVisible());
  assert.equal(
    await page
      .getByRole("button", { name: "Применить оплаты", exact: true })
      .count(),
    0,
  );
  await page
    .getByRole("button", { name: "Проверить оплаты", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Применить оплаты", exact: true })
    .waitFor();
  console.log(
    "PASS: preview/apply, encoding reset, row errors, authenticated LMS filters, lazy contacts, create/archive, catalog import/export, KAM permissions",
  );
} finally {
  await browser.close();
}
