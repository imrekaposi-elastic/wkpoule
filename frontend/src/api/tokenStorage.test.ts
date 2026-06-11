import { describe, expect, it } from "vitest";

import {
  decodeJwtPayload,
  getAccessTokenExpiryMs,
  hasStoredAuthTokens,
  isAccessTokenExpiringSoon,
} from "./tokenStorage";

function makeJwt(payload: Record<string, unknown>): string {
  const encode = (value: object) =>
    btoa(JSON.stringify(value)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode(payload)}.sig`;
}

describe("tokenStorage", () => {
  it("reads exp from access token payload", () => {
    const exp = Math.floor(Date.now() / 1000) + 3600;
    const token = makeJwt({ sub: "1", exp, type: "access" });
    expect(getAccessTokenExpiryMs(token)).toBe(exp * 1000);
    expect(decodeJwtPayload(token)?.type).toBe("access");
  });

  it("detects tokens expiring within the buffer", () => {
    const soon = makeJwt({ exp: Math.floor(Date.now() / 1000) + 30 });
    const later = makeJwt({ exp: Math.floor(Date.now() / 1000) + 600 });
    expect(isAccessTokenExpiringSoon(soon, 120)).toBe(true);
    expect(isAccessTokenExpiringSoon(later, 120)).toBe(false);
  });

  it("reports stored auth tokens", () => {
    localStorage.clear();
    expect(hasStoredAuthTokens()).toBe(false);
    localStorage.setItem("refresh_token", "refresh");
    expect(hasStoredAuthTokens()).toBe(true);
  });
});
