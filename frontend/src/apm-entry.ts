/**
 * Load before main.tsx (see index.html). Elastic recommends initializing RUM before the rest of the app
 * so fetch / history / errors are captured from the start.
 */
import { init as initApm } from "@elastic/apm-rum";
import { APP_VERSION } from "./version";

const w = window as unknown as { __WKPOULE_RUM_INIT__?: boolean };
if (w.__WKPOULE_RUM_INIT__) {
  // Already initialized (e.g. hot reload)
} else {
  w.__WKPOULE_RUM_INIT__ = true;

  // Same-origin proxy (nginx /rum/ → RUM_APM_*). No trailing slash: some URL joiners treat "/intake" as path-absolute.
  const serverUrl = `${window.location.origin}/rum`;
  const environment =
    (import.meta.env.VITE_APM_ENVIRONMENT as string | undefined) ?? "prd";
  const secretToken = (
    import.meta.env.VITE_ELASTIC_APM_RUM_SECRET as string | undefined
  )?.trim();

  initApm({
    serviceName: "wkpoule-frontend",
    serverUrl,
    serviceVersion: APP_VERSION,
    environment,
    ...(secretToken ? { secretToken } : {}),
    ...(import.meta.env.DEV ? { logLevel: "debug" as const } : {}),
  });
}
