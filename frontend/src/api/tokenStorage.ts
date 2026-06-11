/** JWT helpers for client-side expiry checks (signature not verified in the browser). */

export function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(atob(padded)) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function getAccessTokenExpiryMs(token: string): number | null {
  const payload = decodeJwtPayload(token);
  const exp = payload?.exp;
  if (typeof exp !== "number" || !Number.isFinite(exp)) return null;
  return exp * 1000;
}

/** True when the access token is missing, malformed, or within `bufferSeconds` of expiry. */
export function isAccessTokenExpiringSoon(token: string, bufferSeconds = 120): boolean {
  const expMs = getAccessTokenExpiryMs(token);
  if (expMs === null) return true;
  return Date.now() >= expMs - bufferSeconds * 1000;
}

export function hasStoredAuthTokens(): boolean {
  return Boolean(
    localStorage.getItem("access_token") || localStorage.getItem("refresh_token"),
  );
}
