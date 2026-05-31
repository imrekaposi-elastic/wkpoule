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
  field: TeamProfileField,
  lang: SupportedLanguageCode,
): string | null | undefined {
  if (field === "qualification") {
    switch (lang) {
      case "en":
        return team.qualification_en;
      case "nl":
        return team.qualification_nl;
      case "pt":
        return team.qualification_pt;
      case "de":
        return team.qualification_de;
      case "es":
        return team.qualification_es;
      case "it":
        return team.qualification_it;
      case "he":
        return team.qualification_he;
    }
  }

  const detail = team as TeamDetail;
  if (field === "strengths") {
    switch (lang) {
      case "en":
        return detail.strengths_en;
      case "nl":
        return detail.strengths_nl;
      case "pt":
        return detail.strengths_pt;
      case "de":
        return detail.strengths_de;
      case "es":
        return detail.strengths_es;
      case "it":
        return detail.strengths_it;
      case "he":
        return detail.strengths_he;
    }
  }

  switch (lang) {
    case "en":
      return detail.weaknesses_en;
    case "nl":
      return detail.weaknesses_nl;
    case "pt":
      return detail.weaknesses_pt;
    case "de":
      return detail.weaknesses_de;
    case "es":
      return detail.weaknesses_es;
    case "it":
      return detail.weaknesses_it;
    case "he":
      return detail.weaknesses_he;
  }
}

/** Pick localized team profile text with fallback across supported languages. */
export function localizedTeamProfileField(
  team: TeamSummary | TeamDetail,
  field: TeamProfileField,
  language: string,
): string {
  const base = language.split("-")[0] as SupportedLanguageCode;
  const direct = profileValue(team, field, base);
  if (direct) return direct;

  for (const lang of PROFILE_LANGS) {
    const value = profileValue(team, field, lang);
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
