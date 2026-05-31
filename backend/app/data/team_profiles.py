"""Editorial team profiles for the Teams page (seed + DB backfill)."""

from __future__ import annotations

import logging

from app.data.team_profile_i18n import PROFILE_FIELDS, PROFILE_LANGUAGES, merge_locale_overlays
from app.data.team_profiles_data import TEAM_PROFILES
from app.data.team_profiles_de import TEAM_PROFILES_DE
from app.data.team_profiles_es import TEAM_PROFILES_ES
from app.data.team_profiles_he import TEAM_PROFILES_HE
from app.data.team_profiles_it import TEAM_PROFILES_IT
from app.data.team_profiles_pt import TEAM_PROFILES_PT

logger = logging.getLogger(__name__)

ALL_PROFILES = merge_locale_overlays(
    TEAM_PROFILES,
    TEAM_PROFILES_DE,
    TEAM_PROFILES_ES,
    TEAM_PROFILES_HE,
    TEAM_PROFILES_IT,
    TEAM_PROFILES_PT,
)


def build_team_profile(
    name: str,
    fifa_code: str,
    group_letter: str,
    world_ranking: int,
) -> dict[str, str]:
    del name, group_letter, world_ranking
    profile = ALL_PROFILES.get(fifa_code)
    if profile is None:
        logger.warning("No hand-crafted profile for %s; using minimal fallback", fifa_code)
        return _minimal_fallback(fifa_code)
    return dict(profile)


def _minimal_fallback(fifa_code: str) -> dict[str, str]:
    flat: dict[str, str] = {}
    for field in PROFILE_FIELDS:
        for lang in PROFILE_LANGUAGES:
            col = f"{field}_{lang}"
            if lang == "en":
                if field == "qualification":
                    flat[col] = f"{fifa_code} qualified for World Cup 2026."
                elif field == "strengths":
                    flat[col] = "Competitive squad\nTournament motivation"
                else:
                    flat[col] = "Limited profile data available"
            elif lang == "nl":
                if field == "qualification":
                    flat[col] = f"{fifa_code} kwalificeerde zich voor het WK 2026."
                elif field == "strengths":
                    flat[col] = "Competitieve selectie\nToernooi-motivatie"
                else:
                    flat[col] = "Beperkte profielgegevens beschikbaar"
            else:
                flat[col] = flat.get(f"{field}_en", "")
    return flat
