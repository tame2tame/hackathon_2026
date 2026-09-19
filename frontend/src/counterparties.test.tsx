import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { InteractionRows, SignalRow } from "./ConnectedApp";
import { createFixtures, uid } from "./mocks/fixtures";

describe("Контрагенты без вуза и продукта", () => {
  const card = {
    ...createFixtures()[0],
    university: null,
    product: null,
    group: { id: uid(31), code: "b2c", name: "Частные лица (B2C)" },
    counterparty: {
      id: uid(900),
      kind: "person" as const,
      name: "Демо Клиент",
      short_name: "Демо Клиент",
    },
    client: { id: uid(900), kind: "person" as const, name: "Демо Клиент" },
  };
  it("показывает клиента и программу в списке", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <InteractionRows items={[card]} />
      </MemoryRouter>,
    );
    expect(html).toContain("Демо Клиент");
    expect(html).toContain("Без продукта");
    expect(html).not.toContain("undefined");
  });
  it("открывает сигнал клиента без обращения к вузу", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <SignalRow signal={{ ...card.signals[0], interaction: card }} />
      </MemoryRouter>,
    );
    expect(html).toContain("Демо Клиент");
    expect(html).toContain(`/interactions/${card.id}`);
  });
});
