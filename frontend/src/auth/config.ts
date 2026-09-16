export type AuthMode = "mock" | "dev" | "keycloak";
export function resolveMode(
  value: string | undefined,
  development: boolean,
): AuthMode {
  const mode = value || (development ? "mock" : "keycloak");
  if (!["mock", "dev", "keycloak"].includes(mode))
    throw new Error("Некорректный VITE_AUTH_MODE.");
  if (!development && mode !== "keycloak")
    throw new Error("Режимы mock и dev разрешены только в Vite dev.");
  return mode as AuthMode;
}
export const mode = resolveMode(
  import.meta.env.VITE_AUTH_MODE,
  import.meta.env.DEV,
);
export const apiBase = import.meta.env.VITE_API_BASE_URL || "";
