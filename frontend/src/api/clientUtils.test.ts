import { describe, expect, it } from "vitest";

import { shouldAttemptRefresh } from "./clientUtils";

describe("shouldAttemptRefresh", () => {
  it("allows refresh for protected API routes", () => {
    expect(shouldAttemptRefresh("/teams")).toBe(true);
    expect(shouldAttemptRefresh("/api/matches")).toBe(true);
  });

  it("skips refresh for auth endpoints", () => {
    expect(shouldAttemptRefresh("/api/auth/login")).toBe(false);
    expect(shouldAttemptRefresh("/api/auth/register")).toBe(false);
    expect(shouldAttemptRefresh("/api/auth/refresh")).toBe(false);
  });

  it("allows refresh when url is missing", () => {
    expect(shouldAttemptRefresh(undefined)).toBe(true);
  });
});
