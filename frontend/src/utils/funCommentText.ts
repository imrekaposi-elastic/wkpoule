import type { FunComment } from "../types";

/** Pick localized expert commentary; never falls back to German for it/es. */
export function funCommentText(
  fc: FunComment,
  language: string
): string | null {
  const byLang: Record<string, string | undefined> = {
    en: fc.comment_text,
    nl: fc.comment_text_nl,
    pt: fc.comment_text_pt,
    de: fc.comment_text_de,
    it: fc.comment_text_it,
    es: fc.comment_text_es,
  };
  const base = language.split("-")[0];
  return byLang[base] || byLang[language] || fc.comment_text || null;
}
