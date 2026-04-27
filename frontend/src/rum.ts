import { init as initApm } from "@elastic/apm-rum";
import { APP_VERSION } from "./version";

/**
 * Elastic APM RUM: same-origin serverUrl (/rum → nginx → APM Server). Optional secretToken from Vite at build time.
 * Enable RUM on the APM integration / Fleet policy if the server rejects unsigned intake.
 */
export function initRum(): void {
  if (typeof window === "undefined") return;
  const w = window as unknown as { __WKPOULE_RUM_INIT__?: boolean };
  if (w.__WKPOULE_RUM_INIT__) return;
  w.__WKPOULE_RUM_INIT__ = true;

  const serverUrl = `${window.location.origin}/rum`;
  const secret = import.meta.env.VITE_ELASTIC_APM_RUM_SECRET as string | undefined;
  const environment =
    (import.meta.env.VITE_APM_ENVIRONMENT as string | undefined) ?? "prd";

  initApm({
    serviceName: "wkpoule-frontend",
    serverUrl,
    serviceVersion: APP_VERSION,
    environment,
    ...(secret ? { secretToken: secret } : {}),
  });
}
