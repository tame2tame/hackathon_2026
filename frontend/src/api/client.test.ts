import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClient, ApiError, queryString } from "./client";
afterEach(() => vi.unstubAllGlobals());
describe("API v0", () => {
  it("повторяет параметры множественного выбора и сохраняет false", () => {
    expect(
      queryString({
        stage_code: ["signing", "meeting"],
        has_signal: false,
        search: "ИТМО",
      }),
    ).toBe(
      "?stage_code=signing&stage_code=meeting&has_signal=false&search=%D0%98%D0%A2%D0%9C%D0%9E",
    );
  });
  it("передаёт версию и токен только в заголовке", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(new Response("{}", { status: 201 }));
    vi.stubGlobal("fetch", fetcher);
    const api = new ApiClient("http://localhost:8000", async () => ({
      Authorization: "Bearer test-token",
    }));
    await api.transition("id", {
      to_stage_id: "target",
      comment: "Готово",
      expected_version: 3,
      attachment_ids: [],
    });
    const [url, init] = fetcher.mock.calls[0];
    expect(url).not.toContain("test-token");
    expect(init.headers.get("Authorization")).toBe("Bearer test-token");
    expect(JSON.parse(init.body).expected_version).toBe(3);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it("сохраняет problem+json и не повторяет конфликтующий POST", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            code: "INTERACTION_VERSION_CONFLICT",
            status: 409,
            title: "Запись изменена",
            trace_id: "trace",
            errors: [],
          }),
          { status: 409 },
        ),
      );
    vi.stubGlobal("fetch", fetcher);
    const api = new ApiClient("", async () => ({}));
    await expect(
      api.transition("id", {
        to_stage_id: "target",
        comment: "Готово",
        expected_version: 1,
      }),
    ).rejects.toMatchObject({
      code: "INTERACTION_VERSION_CONFLICT",
      status: 409,
      traceId: "trace",
    });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it("обрабатывает не-JSON ошибку прокси без вывода HTML", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response("<html>bad gateway</html>", { status: 502 }),
        ),
    );
    const api = new ApiClient("", async () => ({}));
    await expect(api.me()).rejects.toBeInstanceOf(ApiError);
  });
  it("не превращает отмену запроса в ошибку сервера", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new DOMException("Aborted", "AbortError")),
    );
    const api = new ApiClient("", async () => ({}));
    await expect(api.me()).rejects.toMatchObject({ name: "AbortError" });
  });
});
