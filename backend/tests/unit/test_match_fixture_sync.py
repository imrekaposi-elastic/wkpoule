"""Unit tests for API fixture lookup and winner extraction."""

from datetime import datetime, timezone

from app.models.match import Match
from app.services.match_fixture_sync import (
    find_match_for_api,
    goals_at_90_from_api_score,
    parse_api_kickoff,
    winner_team_id_from_api_score,
)
from tests.seed_fixtures import seed_knockout_match, seed_team, seed_venue


def test_parse_api_kickoff_handles_z_suffix():
    dt = parse_api_kickoff("2026-07-05T19:00:00Z")
    assert dt == datetime(2026, 7, 5, 19, 0, tzinfo=timezone.utc)


def test_winner_team_id_from_api_score_draw_uses_api_side(db):
    home = seed_team(db, fifa_code="NED")
    away = seed_team(db, fifa_code="BEL")
    assert winner_team_id_from_api_score(home.id, away.id, 1, 1, "AWAY_TEAM") == away.id


def test_goals_at_90_prefers_regular_time_over_full_time():
    score = {
        "duration": "PENALTY_SHOOTOUT",
        "fullTime": {"home": 7, "away": 6},
        "regularTime": {"home": 1, "away": 1},
        "extraTime": {"home": 0, "away": 0},
        "penalties": {"home": 6, "away": 5},
    }
    assert goals_at_90_from_api_score(score) == (1, 1)


def test_goals_at_90_falls_back_to_full_time_when_no_regular_time():
    score = {"fullTime": {"home": 2, "away": 1}}
    assert goals_at_90_from_api_score(score) == (2, 1)


def test_goals_at_90_accepts_home_team_away_team_keys():
    score = {
        "fullTime": {"homeTeam": 3, "awayTeam": 2},
        "regularTime": {"homeTeam": 1, "awayTeam": 1},
    }
    assert goals_at_90_from_api_score(score) == (1, 1)


def test_find_match_for_api_assigns_teams_on_knockout_kickoff(db):
    venue = seed_venue(db)
    home = seed_team(db, fifa_code="NED")
    away = seed_team(db, fifa_code="BEL")
    kickoff = datetime(2026, 7, 5, 19, 0, tzinfo=timezone.utc)
    match = Match(
        match_number=89,
        stage="round_of_16",
        group_letter=None,
        home_team_id=None,
        away_team_id=None,
        venue_id=venue.id,
        kickoff_utc=kickoff,
        status="upcoming",
    )
    db.add(match)
    db.commit()

    found = find_match_for_api(
        db,
        home.id,
        away.id,
        "2026-07-05T19:00:00Z",
    )
    assert found is not None
    assert found.id == match.id
    assert found.home_team_id == home.id
    assert found.away_team_id == away.id


def test_find_match_for_api_prefers_existing_team_pair(db):
    match = seed_knockout_match(
        db,
        match_number=90,
        home_code="MEX",
        away_code="CAN",
        kickoff=datetime(2026, 7, 6, 19, 0, tzinfo=timezone.utc),
    )
    home = match.home_team_id
    away = match.away_team_id

    found = find_match_for_api(
        db,
        home,
        away,
        "2026-07-06T19:00:00Z",
    )
    assert found is not None
    assert found.id == match.id
