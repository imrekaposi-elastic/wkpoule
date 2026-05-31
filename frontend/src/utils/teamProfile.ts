import type { SupportedLanguageCode } from "../i18n/languages";
import type { TeamDetail, TeamSummary } from "../types";

const PROFILE_LANGS: SupportedLanguageCode[] = [
  "en",
  "nl",
  "pt",
  "de",
  "he",
  "it",
  "es",
];

export type TeamProfileField = "qualification" | "strengths" | "weaknesses";

function profileValue(
  team: TeamSummary | TeamDetail,
  key: string,
): string | null | undefined {
  return (team as Record<string, string | null | undefined>)[key];
}

/** Pick localized team profile text with fallback across supported languages. */
export function localizedTeamProfileField(
  team: TeamSummary | TeamDetail,
  field: TeamProfileField,
  language: string,
): string {
  const base = language.split("-")[0] as SupportedLanguageCode;
  const preferred = `${field}_${base}`;
  const direct = profileValue(team, preferred);
  if (direct) return direct;

  for (const lang of PROFILE_LANGS) {
    const value = profileValue(team, `${field}_${lang}`);
    if (value) return value;
  }
  return "";
}

export function teamProfileBulletLines(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}
