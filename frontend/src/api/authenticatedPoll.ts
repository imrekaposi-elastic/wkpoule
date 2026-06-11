import { ensureFreshAccessToken, hasStoredAuthTokens } from "./client";

/** Skip background polls when logged out or the tab is hidden. */
export function shouldSkipAuthenticatedPoll(): boolean {
  if (typeof document !== "undefined" && document.visibilityState !== "visible") {
    return true;
  }
  return !hasStoredAuthTokens();
}

/** Refresh the access token if needed; return false when polling should be skipped. */
export async function beforeAuthenticatedPoll(): Promise<boolean> {
  if (shouldSkipAuthenticatedPoll()) return false;
  const token = await ensureFreshAccessToken();
  return token !== null;
}
