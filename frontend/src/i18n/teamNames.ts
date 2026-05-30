import type { Team } from "../types";
import { resolveLocale } from "./languages";

const FIFA_TO_REGION: Record<string, string> = {
  MEX: "MX",
  RSA: "ZA",
  KOR: "KR",
  CZE: "CZ",
  CAN: "CA",
  BIH: "BA",
  QAT: "QA",
  SUI: "CH",
  BRA: "BR",
  MAR: "MA",
  HAI: "HT",
  USA: "US",
  PAR: "PY",
  AUS: "AU",
  TUR: "TR",
  GER: "DE",
  CUW: "CW",
  CIV: "CI",
  ECU: "EC",
  NED: "NL",
  JPN: "JP",
  SWE: "SE",
  TUN: "TN",
  BEL: "BE",
  EGY: "EG",
  IRN: "IR",
  NZL: "NZ",
  ESP: "ES",
  CPV: "CV",
  KSA: "SA",
  URU: "UY",
  FRA: "FR",
  SEN: "SN",
  IRQ: "IQ",
  NOR: "NO",
  ARG: "AR",
  ALG: "DZ",
  AUT: "AT",
  JOR: "JO",
  POR: "PT",
  COD: "CD",
  UZB: "UZ",
  COL: "CO",
  CRO: "HR",
  GHA: "GH",
  PAN: "PA",
};

const SUBDIVISION_NAMES: Record<string, Record<string, string>> = {
  ENG: {
    en: "England",
    nl: "Engeland",
    pt: "Inglaterra",
    de: "England",
    he: "אנגליה",
    it: "Inghilterra",
    es: "Inglaterra",
  },
  SCO: {
    en: "Scotland",
    nl: "Schotland",
    pt: "Escócia",
    de: "Schottland",
    he: "סקוטלנד",
    it: "Scozia",
    es: "Escocia",
  },
};

const VENUE_COUNTRY_TO_REGION: Record<string, string> = {
  Canada: "CA",
  Mexico: "MX",
  USA: "US",
};

function baseLanguage(language: string): string {
  return language.split("-")[0] || "en";
}

function localeFor(language: string): string {
  return resolveLocale(baseLanguage(language));
}

function regionDisplayName(regionCode: string, language: string): string | null {
  try {
    return new Intl.DisplayNames([localeFor(language)], { type: "region" }).of(regionCode) ?? null;
  } catch {
    return null;
  }
}

export function localizedTeamName(
  fifaCode: string | null | undefined,
  fallbackName: string | null | undefined,
  language: string
): string {
  if (!fifaCode) return fallbackName || "";

  const subdivisionName = SUBDIVISION_NAMES[fifaCode]?.[baseLanguage(language)];
  if (subdivisionName) return subdivisionName;

  const regionCode = FIFA_TO_REGION[fifaCode];
  if (!regionCode) return fallbackName || fifaCode;

  return regionDisplayName(regionCode, language) || fallbackName || fifaCode;
}

export function localizedTeam(team: Team | null | undefined, language: string): string {
  return localizedTeamName(team?.fifa_code, team?.name, language);
}

export function localizedVenueCountry(country: string, language: string): string {
  const regionCode = VENUE_COUNTRY_TO_REGION[country];
  if (!regionCode) return country;

  return regionDisplayName(regionCode, language) || country;
}
