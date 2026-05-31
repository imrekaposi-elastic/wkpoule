"""Unit tests for static team data loaders."""

from app.data.team_profiles import build_team_profile
from app.data.team_qualification_data import build_qualification_data
from app.data.team_squads import build_team_squad


def test_build_qualification_data_for_known_team():
    data = build_qualification_data("NED")

    assert data is not None
    assert data["standings"]
    assert data["competition"]


def test_build_team_squad_returns_real_players_for_known_team():
    squad = build_team_squad("NED", "Netherlands", 7)

    assert len(squad) >= 20
    assert squad[0]["name"]
    assert squad[0]["position"] in {"GK", "DF", "MF", "FW"}


def test_build_team_profile_uses_fallback_for_unknown_team():
    profile = build_team_profile("Unknown", "ZZZ", "Z", 999)

    assert profile["qualification_en"].startswith("ZZZ qualified")
    assert profile["qualification_nl"].startswith("ZZZ kwalificeerde")
