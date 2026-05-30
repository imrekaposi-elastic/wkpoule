from types import SimpleNamespace

from app.services.team_names import localized_team_name, team_matches_search


def _team(fifa_code: str, name: str) -> SimpleNamespace:
    return SimpleNamespace(fifa_code=fifa_code, name=name)


def test_localized_team_name_dutch_germany():
    assert localized_team_name("GER", "Germany", "nl") == "Duitsland"


def test_team_matches_search_finds_dutch_name():
    team = _team("GER", "Germany")
    assert team_matches_search(team, "duitsland")
    assert team_matches_search(team, "DUITSLAND")
    assert not team_matches_search(team, "brazil")


def test_team_matches_search_finds_english_name():
    team = _team("NED", "Netherlands")
    assert team_matches_search(team, "netherlands")
    assert team_matches_search(team, "nederland")
