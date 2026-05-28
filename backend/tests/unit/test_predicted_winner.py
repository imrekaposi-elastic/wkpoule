"""Unit tests for knockout winner resolution including advance pick."""

from types import SimpleNamespace

from app.services.prediction_advance import predicted_winner_team_id


def _team(team_id: int, ranking: int):
    return SimpleNamespace(id=team_id, world_ranking=ranking)


def test_draw_uses_advance_team_when_set():
    teams = {1: _team(1, 20), 2: _team(2, 5)}
    assert predicted_winner_team_id(1, 2, 1, 1, teams, 2) == 2


def test_draw_falls_back_to_fifa_ranking():
    teams = {1: _team(1, 3), 2: _team(2, 15)}
    assert predicted_winner_team_id(1, 2, 0, 0, teams, None) == 1
