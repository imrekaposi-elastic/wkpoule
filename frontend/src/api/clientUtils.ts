/** Auth URL paths where a 401 should not trigger token refresh. */
export function shouldAttemptRefresh(url: string | undefined): boolean {
  if (!url) return true;
  return (
    !url.includes("/auth/login") &&
    !url.includes("/auth/register") &&
    !url.includes("/auth/refresh")
  );
}
