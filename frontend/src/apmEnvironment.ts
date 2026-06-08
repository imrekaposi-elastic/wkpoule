export type RuntimeConfig = {
  environment?: string;
};

/** Resolve Elastic RUM environment: runtime ConfigMap wins over build-time Vite, then hostname. */
export function resolveApmEnvironment(
  hostname: string,
  runtimeEnvironment?: string,
  buildEnvironment?: string,
): string {
  const runtime = runtimeEnvironment?.trim();
  if (runtime) return runtime;

  const build = buildEnvironment?.trim();
  if (build) return build;

  if (hostname.startsWith("acc-")) return "acc";

  return "prd";
}
