import type { ApiClient } from "./client";

export const interactionQueryOptions = (api: ApiClient, id: string) => ({
  // Версию карточки обновляем явно: смена вкладки не должна подменять expected_version.
  refetchOnWindowFocus: false,
  refetchOnReconnect: false,
  queryKey: ["interaction", id],
  queryFn: ({ signal }: { signal: AbortSignal }) => api.interaction(id, signal),
});
