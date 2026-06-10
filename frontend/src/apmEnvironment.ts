export type RuntimeConfig = {
  environment?: string;
};

/** Resolve Elastic RUM environment: runtime ConfigMap, then hostname, then build-time Vite. */
export function resolveApmEnvironment(
  hostname: string,
  runtimeEnvironment?: string,
  buildEnvironment?: string,
): string {
  const runtime = runtimeEnvironment?.trim();
  if (runtime) return runtime;

  if (hostname.startsWith("acc-")) return "acc";

  const build = buildEnvironment?.trim();
  if (build) return build;

  return "prd";
}
