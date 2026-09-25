import { afterEach, expect, it, vi } from "vitest";
import { ApiClient } from "./client";
afterEach(() => vi.unstubAllGlobals());
it("отправляет multipart без JSON Content-Type и принимает пустой ответ", async () => {
  const fetcher = vi
    .fn()
    .mockResolvedValue(new Response(null, { status: 204 }));
  vi.stubGlobal("fetch", fetcher);
  const api = new ApiClient("", async () => ({ Authorization: "Bearer demo" }));
  const body = new FormData();
  body.append("file", new Blob(["test"]), "test.csv");
  await api.upload("/api/v1/imports", body);
  expect(fetcher.mock.calls[0][1].headers.has("Content-Type")).toBe(false);
  expect(fetcher.mock.calls[0][1].body).toBe(body);
});
it("скачивает файл с авторизацией и сохраняет ошибку API", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ detail: "Файл ещё не готов", code: "NOT_FOUND" }),
          { status: 404 },
        ),
      ),
  );
  const api = new ApiClient("", async () => ({}));
  await expect(api.file("/api/v1/reports/id/file")).rejects.toMatchObject({
    message: "Файл ещё не готов",
    status: 404,
  });
});
it("читает разделённые UTF-8 события SSE и отправляет Last-Event-ID в заголовке", async () => {
  const encoder = new TextEncoder();
  const bytes = encoder.encode(
    'id: 42\nevent: report.updated\ndata: {"text":"готово"}\n\n',
  );
  const stream = new ReadableStream({
    start(c) {
      c.enqueue(bytes.slice(0, 12));
      c.enqueue(bytes.slice(12, 57));
      c.enqueue(bytes.slice(57));
      c.close();
    },
  });
  const fetcher = vi.fn().mockResolvedValue(new Response(stream));
  vi.stubGlobal("fetch", fetcher);
  const api = new ApiClient("", async () => ({ Authorization: "Bearer demo" }));
  const events: string[] = [];
  const cursor = await api.events(
    new AbortController().signal,
    (e) => events.push(e),
    "41",
  );
  expect(events).toEqual(["report.updated"]);
  expect(cursor).toBe("42");
  expect(fetcher.mock.calls[0][1].headers["Last-Event-ID"]).toBe("41");
  expect(fetcher.mock.calls[0][0]).not.toContain("demo");
});
