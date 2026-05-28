/** Format API stage slug (e.g. round_of_16) for display without regex on untrusted input. */
export function formatStageSlug(stage: string): string {
  return stage
    .split("_")
    .filter((part) => part.length > 0)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function formatStageSlugSpacesOnly(stage: string): string {
  return stage.split("_").join(" ");
}
