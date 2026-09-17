import { afterEach, describe, expect, it, vi } from "vitest";

const oidc = vi.hoisted(() => ({
  authenticated: true,
  token: "synthetic-token",
  init: vi.fn().mockResolvedValue(true),
  updateToken: vi.fn().mockResolvedValue(false),
  clearToken: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}));
vi.mock("keycloak-js", () => ({
  default: vi.fn(function () {
    return oidc;
  }),
}));
afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
  vi.clearAllMocks();
  oidc.authenticated = true;
  oidc.token = "synthetic-token";
  oidc.updateToken.mockResolvedValue(false);
});
describe("заголовки сессии", () => {
  it("dev отправляет X-Dev-User без Authorization и без Keycloak", async () => {
    vi.stubEnv("VITE_AUTH_MODE", "dev");
    const session = await import("./session");
    await session.initializeSession();
    session.setDevUser("roman.kovalev@example.com");
    expect(await session.authHeaders()).toEqual({
      "X-Dev-User": "roman.kovalev@example.com",
    });
    expect(oidc.init).not.toHaveBeenCalled();
  });
  it("Keycloak запускается один раз с PKCE и обновляет токен перед запросом", async () => {
    vi.stubEnv("VITE_AUTH_MODE", "keycloak");
    const session = await import("./session");
    await Promise.all([
      session.initializeSession(),
      session.initializeSession(),
    ]);
    expect(oidc.init).toHaveBeenCalledTimes(1);
    expect(oidc.init).toHaveBeenCalledWith(
      expect.objectContaining({ pkceMethod: "S256", responseMode: "query" }),
    );
    expect(await session.authHeaders()).toEqual({
      Authorization: "Bearer synthetic-token",
    });
    expect(oidc.updateToken).toHaveBeenCalledWith(30);
  });
  it("не подменяет завершённую сессию режимом dev", async () => {
    vi.stubEnv("VITE_AUTH_MODE", "keycloak");
    const session = await import("./session");
    await session.initializeSession();
    oidc.updateToken.mockRejectedValueOnce(new Error("expired"));
    await expect(session.authHeaders()).rejects.toMatchObject({
      status: 401,
      code: "AUTH_REQUIRED",
    });
    expect(oidc.clearToken).toHaveBeenCalledOnce();
  });
});
