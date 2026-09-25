import { expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Address } from "./Communication";
it("все hover-состояния основных кнопок исключают disabled", () => {
  for (const file of ["styles.css", "brandbook.css", "service.css"]) {
    const css = readFileSync(new URL("../" + file, import.meta.url), "utf8");
    for (const match of css.matchAll(/\.button-primary:hover([^{}]*)\{/g))
      expect(match[1]).toContain(":not(:disabled)");
  }
});
it("канал доставки имеет доступный переключатель и не предлагает сохранить пустой адрес", () => {
  const client = new QueryClient();
  const html = renderToStaticMarkup(
    <QueryClientProvider client={client}>
      <Address
        item={{
          channel_kind: "email",
          channel_name: "Электронная почта",
          address: null,
          is_enabled: false,
          channel_enabled: true,
        }}
      />
    </QueryClientProvider>,
  );
  expect(html).toContain('role="switch"');
  expect(html).toContain('aria-checked="false"');
  expect(html).not.toContain('type="checkbox"');
  expect(html).toMatch(/disabled=""[^>]*>Сохранить/);
  client.clear();
});
it("мобильные кнопки заголовков сохраняют видимые текстовые подписи", () => {
  const css = readFileSync(
    new URL("../brandbook.css", import.meta.url),
    "utf8",
  );
  expect(css).not.toMatch(
    /\.section-heading \.button\s*\{[^}]*font-size:\s*0\s*;/,
  );
});
