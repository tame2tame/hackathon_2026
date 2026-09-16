import Keycloak from "keycloak-js";
import { mode } from "./config";
import { ApiError } from "../api/client";
let keycloak: Keycloak | undefined;
let start: Promise<boolean> | undefined;
export const devUsers = [
  { email: "anna.smirnova@example.com", name: "Анна Смирнова" },
  { email: "mikhail.volkov@example.com", name: "Михаил Волков" },
  { email: "roman.kovalev@example.com", name: "Роман Ковалёв" },
  { email: "alina.denisova@example.com", name: "Алина Денисова" },
];
let devUser = import.meta.env.VITE_DEV_USER || devUsers[0].email;
export const currentDevUser = () => devUser;
export const setDevUser = (value: string) => {
  devUser = value;
};
export function initializeSession(): Promise<boolean> {
  if (mode !== "keycloak") return Promise.resolve(true);
  if (!start) {
    keycloak = new Keycloak({
      url: import.meta.env.VITE_KEYCLOAK_URL || "http://127.0.0.1:8080",
      realm: import.meta.env.VITE_KEYCLOAK_REALM || "radar-vuzov",
      clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "radar-web",
    });
    start = keycloak.init({
      onLoad: "check-sso",
      pkceMethod: "S256",
      checkLoginIframe: false,
      responseMode: "query",
    });
  }
  return start;
}
export async function authHeaders(): Promise<Record<string, string>> {
  if (mode !== "keycloak") return { "X-Dev-User": devUser };
  if (!keycloak?.authenticated)
    throw new ApiError(401, "AUTH_REQUIRED", "Войдите через Keycloak.");
  try {
    await keycloak.updateToken(30);
  } catch {
    keycloak.clearToken();
    throw new ApiError(
      401,
      "AUTH_REQUIRED",
      "Сессия завершилась. Войдите снова.",
    );
  }
  if (!keycloak.token)
    throw new ApiError(401, "AUTH_REQUIRED", "Войдите снова.");
  return { Authorization: `Bearer ${keycloak.token}` };
}
export const login = () =>
  keycloak?.login({ redirectUri: window.location.origin + "/radar" });
export const logout = () =>
  keycloak?.logout({ redirectUri: window.location.origin + "/" });
