import { beforeAll, afterAll, afterEach, describe, expect, it } from "vitest";
import { setupServer } from "msw/node";
import { handlers, resetFixtures } from "./handlers";
import { ApiClient } from "../api/client";
import {
  QueryClient,
  QueryObserver,
  focusManager,
} from "@tanstack/react-query";
import { interactionQueryOptions } from "../api/queries";
import { uid } from "./fixtures";
const server = setupServer(...handlers);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  resetFixtures();
});
afterAll(() => server.close());
const api = (email = "anna.smirnova@example.com") =>
  new ApiClient("http://localhost:8000", async () => ({ "X-Dev-User": email }));
describe("клиент на MSW-контракте", () => {
  it("считывает профиль, несколько сигналов на запись и настоящую пагинацию", async () => {
    expect((await api().me()).role).toBe("kam");
    expect((await api("alina.denisova@example.com").signals()).total).toBe(7);
    const p = await api().interactions({ page: 2, page_size: 2 });
    expect(p.items).toHaveLength(2);
    expect(p.total).toBe(4);
    expect(p.page).toBe(2);
  });
  it("скрывает чужую запись одинаково для чтения и записи", async () => {
    await expect(api().interaction(uid(202))).rejects.toMatchObject({
      status: 404,
      code: "NOT_FOUND",
    });
    await expect(
      api().transition(uid(202), {
        to_stage_id: uid(107),
        comment: "Готово",
        expected_version: 1,
      }),
    ).rejects.toMatchObject({ status: 404 });
  });
  it("следует допустимым переходам, сохраняет историю и обрабатывает устаревшую версию", async () => {
    const card = await api().interaction(uid(200));
    const payload = {
      to_stage_id: card.allowed_transitions[0].to_stage.id,
      comment: "Договор согласован",
      expected_version: card.version,
    };
    const result = await api().transition(card.id, payload);
    expect(result.interaction.version).toBe(2);
    expect(result.interaction.history[0].comment).toBe(payload.comment);
    expect(result.interaction.signals).toHaveLength(0);
    await expect(api().transition(card.id, payload)).rejects.toMatchObject({
      code: "INTERACTION_VERSION_CONFLICT",
    });
  });
  it("две вкладки: возврат фокуса не заменяет версию перед отправкой перехода", async () => {
    const first = api();
    const second = api();
    const cache = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: 0 } },
    });
    const options = interactionQueryOptions(second, uid(200));
    const observer = new QueryObserver(cache, options);
    cache.mount();
    const unsubscribe = observer.subscribe(() => {});
    try {
      await cache.fetchQuery(options);
      const card = await first.interaction(uid(200));
      const payload = {
        to_stage_id: card.allowed_transitions[0].to_stage.id,
        comment: "Проверка двух вкладок",
        expected_version: card.version,
      };
      await first.transition(card.id, payload);
      focusManager.setFocused(false);
      focusManager.setFocused(true);
      await new Promise((resolve) => setTimeout(resolve, 30));
      const visibleCard = observer.getCurrentResult().data!;
      expect(visibleCard.version).toBe(card.version);
      await expect(
        second.transition(card.id, {
          ...payload,
          expected_version: visibleCard.version,
        }),
      ).rejects.toMatchObject({
        status: 409,
        code: "INTERACTION_VERSION_CONFLICT",
      });
      await observer.refetch();
      expect(observer.getCurrentResult().data!.version).toBe(card.version + 1);
    } finally {
      unsubscribe();
      cache.unmount();
      cache.clear();
      focusManager.setFocused(undefined);
    }
  });
  it("не скрывает лицензию после смены этапа", async () => {
    const card = await api().interaction(uid(201));
    const result = await api().transition(card.id, {
      to_stage_id: card.allowed_transitions[0].to_stage.id,
      comment: "Готово",
      expected_version: 1,
    });
    expect(result.interaction.signals[0].kind).toBe("license_expiring");
  });
  it("фильтрует по UUID вуза и коду этапа", async () => {
    expect(
      (
        await api().interactions({
          university_id: [uid(300)],
          stage_code: ["signing"],
        })
      ).items[0].id,
    ).toBe(uid(200));
    expect((await api().university(uid(300))).interactions_count).toBe(1);
  });
});
