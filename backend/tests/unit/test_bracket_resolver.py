"""Unit tests for knockout tie-break logic."""

from types import SimpleNamespace

from app.services.bracket_resolver import _winner_from_scores


def _team(team_id: int, ranking: int):
    return SimpleNamespace(id=team_id, world_ranking=ranking)


def test_winner_from_scores_home_win():
    teams = {1: _team(1, 5), 2: _team(2, 10)}
    assert _winner_from_scores(1, 2, 2, 0, teams) == 1


def test_winner_from_scores_away_win():
    teams = {1: _team(1, 5), 2: _team(2, 10)}
    assert _winner_from_scores(1, 2, 0, 1, teams) == 2


def test_winner_from_scores_draw_uses_fifa_ranking():
    teams = {1: _team(1, 3), 2: _team(2, 15)}
    assert _winner_from_scores(1, 2, 1, 1, teams) == 1

    teams = {1: _team(1, 20), 2: _team(2, 5)}
    assert _winner_from_scores(1, 2, 2, 2, teams) == 2
