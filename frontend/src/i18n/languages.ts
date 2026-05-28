/** Shared language codes and Intl locale tags for the UI. */
export const SUPPORTED_LANGUAGE_CODES = [
  "en",
  "nl",
  "pt",
  "de",
  "he",
  "it",
  "es",
] as const;

export type SupportedLanguageCode = (typeof SUPPORTED_LANGUAGE_CODES)[number];

export const LOCALE_MAP: Record<string, string> = {
  en: "en-US",
  nl: "nl-NL",
  pt: "pt-BR",
  de: "de-DE",
  he: "he-IL",
  it: "it-IT",
  es: "es-ES",
};

export function resolveLocale(language: string): string {
  return LOCALE_MAP[language] || "en-US";
}
