/** Auth URL paths where a 401 should not trigger token refresh. */
export function shouldAttemptRefresh(url: string | undefined): boolean {
  if (!url) return true;
  return !isAuthEndpoint(url);
}

/** Login/register/refresh must not run proactive token refresh in the request interceptor. */
export function isAuthEndpoint(url: string | undefined): boolean {
  if (!url) return false;
  return (
    url.includes("/auth/login") ||
    url.includes("/auth/register") ||
    url.includes("/auth/refresh")
  );
}
