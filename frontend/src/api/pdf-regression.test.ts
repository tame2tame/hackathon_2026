import { afterEach, expect, it, vi } from "vitest";
import { ApiClient } from "./client";
afterEach(() => vi.unstubAllGlobals());
it.each(["application/json", "text/html"])(
  "не сохраняет %s вместо PDF",
  async (type) => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response("{}", { headers: { "Content-Type": type } }),
        ),
    );
    await expect(
      new ApiClient("", async () => ({})).file(
        "/api/v1/analytics/stats/report",
        "pdf",
      ),
    ).rejects.toThrow("PDF");
  },
);
it("проверяет сигнатуру PDF, а не только MIME", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response("broken", {
        headers: { "Content-Type": "application/pdf" },
      }),
    ),
  );
  await expect(
    new ApiClient("", async () => ({})).file("/report", "pdf"),
  ).rejects.toThrow("PDF");
});
it("принимает корректный PDF без изменения байтов", async () => {
  const text = "%PDF-1.4\nfixture\n%%EOF\n";
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        new Response(text, { headers: { "Content-Type": "application/pdf" } }),
      ),
  );
  expect(
    await (
      await new ApiClient("", async () => ({})).file("/report", "pdf")
    ).text(),
  ).toBe(text);
});
