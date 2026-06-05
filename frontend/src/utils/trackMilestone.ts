import { apm } from "@elastic/apm-rum";

/** Emit RUM custom transactions for Elastic conversion-goal dashboards. */
export function trackMilestones(keys: string[] | undefined): void {
  if (!keys?.length) return;
  for (const key of keys) {
    const tx = apm.startTransaction(`goal:${key}`, "user-interaction");
    if (tx) {
      tx.addLabels({ milestone: key });
      tx.end();
    }
  }
}
