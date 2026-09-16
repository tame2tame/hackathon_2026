import { describe, expect, it } from "vitest";
import { resolveMode } from "./config";
describe("режим доступа", () => {
  it("production всегда требует Keycloak", () => {
    expect(resolveMode(undefined, false)).toBe("keycloak");
    expect(() => resolveMode("dev", false)).toThrow();
    expect(() => resolveMode("mock", false)).toThrow();
  });
  it("моки доступны только при явном dev-режиме", () => {
    expect(resolveMode(undefined, true)).toBe("mock");
    expect(resolveMode("dev", true)).toBe("dev");
  });
  it("опечатка в настройке не отключает авторизацию", () => {
    expect(() => resolveMode("deev", true)).toThrow();
  });
});
