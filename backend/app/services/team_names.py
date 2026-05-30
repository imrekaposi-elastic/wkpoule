"""Localized team display names and multilingual search aliases."""

from __future__ import annotations

from babel import Locale
from babel.core import UnknownLocaleError

from app.models.team import Team

FIFA_TO_REGION: dict[str, str] = {
    "MEX": "MX",
    "RSA": "ZA",
    "KOR": "KR",
    "CZE": "CZ",
    "CAN": "CA",
    "BIH": "BA",
    "QAT": "QA",
    "SUI": "CH",
    "BRA": "BR",
    "MAR": "MA",
    "HAI": "HT",
    "USA": "US",
    "PAR": "PY",
    "AUS": "AU",
    "TUR": "TR",
    "GER": "DE",
    "CUW": "CW",
    "CIV": "CI",
    "ECU": "EC",
    "NED": "NL",
    "JPN": "JP",
    "SWE": "SE",
    "TUN": "TN",
    "BEL": "BE",
    "EGY": "EG",
    "IRN": "IR",
    "NZL": "NZ",
    "ESP": "ES",
    "CPV": "CV",
    "KSA": "SA",
    "URU": "UY",
    "FRA": "FR",
    "SEN": "SN",
    "IRQ": "IQ",
    "NOR": "NO",
    "ARG": "AR",
    "ALG": "DZ",
    "AUT": "AT",
    "JOR": "JO",
    "POR": "PT",
    "COD": "CD",
    "UZB": "UZ",
    "COL": "CO",
    "CRO": "HR",
    "GHA": "GH",
    "PAN": "PA",
}

SUBDIVISION_NAMES: dict[str, dict[str, str]] = {
    "ENG": {
        "en": "England",
        "nl": "Engeland",
        "pt": "Inglaterra",
        "de": "England",
        "he": "אנגליה",
        "it": "Inghilterra",
        "es": "Inglaterra",
    },
    "SCO": {
        "en": "Scotland",
        "nl": "Schotland",
        "pt": "Escócia",
        "de": "Schottland",
        "he": "סקוטלנד",
        "it": "Scozia",
        "es": "Escocia",
    },
}

SUPPORTED_SEARCH_LANGUAGES = ("en", "nl", "pt", "de", "he", "it", "es")

_locale_cache: dict[str, Locale] = {}


def _base_language(language: str) -> str:
    return (language or "en").split("-")[0].lower()


def _locale_for(language: str) -> Locale:
    base = _base_language(language)
    if base not in _locale_cache:
        try:
            _locale_cache[base] = Locale.parse(base)
        except UnknownLocaleError:
            _locale_cache[base] = Locale.parse("en")
    return _locale_cache[base]


def localized_team_name(fifa_code: str, fallback_name: str, language: str) -> str:
    base = _base_language(language)
    subdivision = SUBDIVISION_NAMES.get(fifa_code, {}).get(base)
    if subdivision:
        return subdivision

    region_code = FIFA_TO_REGION.get(fifa_code)
    if not region_code:
        return fallback_name or fifa_code

    locale = _locale_for(language)
    return locale.territories.get(region_code, fallback_name or fifa_code)


def team_search_aliases(team: Team) -> set[str]:
    aliases = {team.name.lower(), team.fifa_code.lower()}
    for lang in SUPPORTED_SEARCH_LANGUAGES:
        aliases.add(localized_team_name(team.fifa_code, team.name, lang).lower())
    return aliases


def team_matches_search(team: Team | None, term: str) -> bool:
    if team is None:
        return False
    needle = term.strip().lower()
    if not needle:
        return True
    return any(needle in alias for alias in team_search_aliases(team))
