import { beforeAll, afterAll, expect, it } from "vitest";
import { setupServer } from "msw/node";
import { handlers } from "./handlers";
import { ApiClient } from "../api/client";
import type { Schema } from "../api/types";
import { uid } from "./fixtures";
import { pdfFromJpegs } from "./stats-report";
const server = setupServer(...handlers);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());
const client = (email = "anna.smirnova@example.com") =>
  new ApiClient("http://localhost", async () => ({ "X-Dev-User": email }));
it("статистика использует историю длительности и объединяет одинаковые направления", async () => {
  const api = client();
  const duration = await api.get<Schema["ChartOut"]>(
    "/analytics/stats/stage-durations",
  );
  const distribution = await api.get<Schema["ChartOut"]>(
    "/analytics/stats/distribution",
  );
  expect(Math.max(...duration.values)).toBeGreaterThan(1);
  expect(new Set(distribution.labels).size).toBe(distribution.labels.length);
  expect(distribution.values.reduce((a, b) => a + b, 0)).toBe(4);
});
it("срез B2C использует свои этапы", async () => {
  const chart = await client("mikhail.volkov@example.com").get<
    Schema["ChartOut"]
  >("/analytics/stats/funnel", { group_id: uid(31) });
  expect(chart.labels).toEqual(["Заявка", "Зачисление"]);
});
it("сохраняет адрес и состояние канала отдельно для каждого пользователя", async () => {
  const api = client();
  await api.send(
    "/me/notification-addresses/email",
    { address: "demo@example.com", is_enabled: true },
    "PUT",
  );
  const mine = await api.get<Schema["AddressOut"][]>(
    "/me/notification-addresses",
  );
  const other = await client("mikhail.volkov@example.com").get<
    Schema["AddressOut"][]
  >("/me/notification-addresses");
  expect(mine.find((a) => a.channel_kind === "email")).toMatchObject({
    address: "demo@example.com",
    is_enabled: true,
  });
  expect(other.find((a) => a.channel_kind === "email")?.address).toBeNull();
});
it("PDF содержит точные байтовые смещения объектов и завершающий маркер", () => {
  const pdf = pdfFromJpegs([new Uint8Array([255, 216, 255, 217])], 1, 1);
  const text = new TextDecoder().decode(pdf);
  expect(text.startsWith("%PDF-1.4")).toBe(true);
  expect(text.endsWith("%%EOF\n")).toBe(true);
  const xref = Number(text.match(/startxref\n(\d+)/)?.[1]);
  expect(new TextDecoder().decode(pdf.slice(xref, xref + 4))).toBe("xref");
  const offsets = [...text.matchAll(/(\d{10}) 00000 n/g)].map((m) =>
    Number(m[1]),
  );
  offsets.forEach((offset, i) =>
    expect(new TextDecoder().decode(pdf.slice(offset, offset + 7))).toBe(
      `${i + 1} 0 obj`,
    ),
  );
});
