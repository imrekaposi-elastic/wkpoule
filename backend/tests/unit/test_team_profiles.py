"""Unit tests for editorial team profile data."""

from app.data.team_profile_i18n import PROFILE_FIELDS, PROFILE_LANGUAGES
from app.data.team_profiles import ALL_PROFILES, build_team_profile


def test_all_teams_have_full_locale_profiles():
    assert len(ALL_PROFILES) == 48
    for fifa_code, profile in ALL_PROFILES.items():
        for field in PROFILE_FIELDS:
            for lang in PROFILE_LANGUAGES:
                key = f"{field}_{lang}"
                assert profile.get(key), f"{fifa_code} missing {key}"


def test_build_team_profile_returns_flat_columns_for_known_team():
    profile = build_team_profile("Netherlands", "NED", "F", 7)

    assert profile["qualification_en"]
    assert profile["qualification_he"]
    assert profile["strengths_de"]
    assert profile["weaknesses_it"]
    assert "qualification_en" in profile
    assert len(profile) == len(PROFILE_FIELDS) * len(PROFILE_LANGUAGES)
