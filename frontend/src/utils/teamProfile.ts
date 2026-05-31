import type { SupportedLanguageCode } from "./languages";

const PROFILE_FIELDS = ["qualification", "strengths", "weaknesses"] as const;
const PROFILE_LANGS: SupportedLanguageCode[] = [
  "en",
  "nl",
  "pt",
  "de",
  "he",
  "it",
  "es",
];

export type TeamProfileField = (typeof PROFILE_FIELDS)[number];

type TeamProfileRecord = Record<string, string | null | undefined>;

/** Pick localized team profile text with en → nl fallback chain. */
export function localizedTeamProfileField(
  team: TeamProfileRecord,
  field: TeamProfileField,
  language: string,
): string {
  const base = language.split("-")[0] as SupportedLanguageCode;
  const preferred = `${field}_${base}`;
  if (team[preferred]) return team[preferred] as string;

  for (const lang of PROFILE_LANGS) {
    const key = `${field}_${lang}`;
    const value = team[key];
    if (value) return value as string;
  }
  return "";
}

export function teamProfileBulletLines(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}
