import { describe, expect, it } from "vitest";

import { isAuthEndpoint, shouldAttemptRefresh } from "./clientUtils";

describe("clientUtils", () => {
  it("treats login, register, and refresh as auth endpoints", () => {
    expect(isAuthEndpoint("/auth/login")).toBe(true);
    expect(isAuthEndpoint("/auth/register")).toBe(true);
    expect(isAuthEndpoint("/auth/refresh")).toBe(true);
    expect(isAuthEndpoint("/auth/me")).toBe(false);
    expect(isAuthEndpoint("/subgroups/mine")).toBe(false);
  });

  it("does not refresh on auth endpoints", () => {
    expect(shouldAttemptRefresh("/auth/login")).toBe(false);
    expect(shouldAttemptRefresh("/subgroups/mine")).toBe(true);
  });
});
