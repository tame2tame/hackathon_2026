import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ConnectedApp from "./ConnectedApp";
import { mode } from "./auth/config";
import "./styles.css";
import "./brandbook.css";
const client = new QueryClient({
  defaultOptions: {
    queries: { retry: false, staleTime: 15_000, refetchOnWindowFocus: true },
    mutations: { retry: false },
  },
});
async function bootstrap() {
  if (import.meta.env.DEV && mode === "mock") {
    const { worker } = await import("./mocks/browser");
    await worker.start({
      quiet: true,
      onUnhandledRequest(request) {
        if (new URL(request.url).pathname.startsWith("/api/"))
          throw new Error("Для метода API не определён мок.");
      },
    });
  }
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <QueryClientProvider client={client}>
        <BrowserRouter>
          <ConnectedApp />
        </BrowserRouter>
      </QueryClientProvider>
    </React.StrictMode>,
  );
}
bootstrap().catch(() => {
  const root = document.getElementById("root");
  if (root)
    root.textContent =
      "Не удалось запустить приложение. Проверьте конфигурацию режима и доступность Service Worker, затем обновите страницу.";
});

import "./service.css";
