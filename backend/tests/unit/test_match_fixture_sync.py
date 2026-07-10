"""Unit tests for API fixture lookup and winner extraction."""

from datetime import datetime, timezone

from app.models.match import Match
from app.services.match_fixture_sync import (
    advancing_team_id_from_api_score,
    advancing_team_id_from_api_winner,
    find_match_for_api,
    goals_at_90_for_match,
    goals_at_90_from_api_score,
    map_api_goals_to_match_orientation,
    parse_api_kickoff,
    winner_team_id_from_api_score,
    _kickoff_utc,
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


def test_goals_at_90_derives_from_full_time_minus_extra_time_when_regular_time_null():
    """ARG vs CPV: API regularTime null, fullTime 3-2 after extraTime 2-1."""
    score = {
        "winner": "HOME_TEAM",
        "duration": "EXTRA_TIME",
        "fullTime": {"home": 3, "away": 2},
        "regularTime": {"home": None, "away": None},
        "extraTime": {"home": 2, "away": 1},
        "halfTime": {"home": 1, "away": 0},
    }
    assert goals_at_90_from_api_score(score) == (1, 1)


def test_goals_at_90_accepts_home_team_away_team_keys():
    score = {
        "fullTime": {"homeTeam": 3, "awayTeam": 2},
        "regularTime": {"homeTeam": 1, "awayTeam": 1},
    }
    assert goals_at_90_from_api_score(score) == (1, 1)


def test_map_api_goals_swapped_when_db_home_away_opposite_api():
    from app.models.match import Match

    match = Match(
        match_number=99,
        stage="round_of_32",
        home_team_id=20,
        away_team_id=10,
        venue_id=1,
        kickoff_utc=datetime(2026, 7, 5, 19, 0, tzinfo=timezone.utc),
        status="upcoming",
    )
    assert map_api_goals_to_match_orientation(match, 10, 20, 1, 1) == (1, 1)
    assert map_api_goals_to_match_orientation(match, 10, 20, 2, 0) == (0, 2)


def test_advancing_team_id_from_api_winner_uses_api_participant_ids():
    assert advancing_team_id_from_api_winner("HOME_TEAM", 10, 20) == 10
    assert advancing_team_id_from_api_winner("AWAY_TEAM", 10, 20) == 20
    assert advancing_team_id_from_api_winner("DRAW", 10, 20) is None


def test_advancing_team_id_from_api_score_egy_aus_null_winner_uses_full_time():
    """Real football-data.org payload: winner null, pens tied, fullTime shows Egypt through."""
    aus_id = 15
    egy_id = 26
    score = {
        "winner": None,
        "duration": "PENALTY_SHOOTOUT",
        "fullTime": {"home": 3, "away": 5},
        "regularTime": {"home": 1, "away": 1},
        "extraTime": {"home": 0, "away": 0},
        "penalties": {"home": 4, "away": 4},
    }
    assert advancing_team_id_from_api_score(score, aus_id, egy_id) == egy_id


def test_advancing_team_id_from_api_score_prefers_penalties_when_decisive():
    score = {
        "winner": None,
        "duration": "PENALTY_SHOOTOUT",
        "fullTime": {"home": 7, "away": 6},
        "regularTime": {"home": 1, "away": 1},
        "penalties": {"home": 6, "away": 5},
    }
    assert advancing_team_id_from_api_score(score, 10, 20) == 10


def test_winner_team_id_from_api_score_draw_uses_api_participant_ids():
    assert winner_team_id_from_api_score(
        20,
        10,
        1,
        1,
        "AWAY_TEAM",
        api_home_id=10,
        api_away_id=20,
    ) == 20


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


def test_find_match_for_api_accepts_swapped_home_away(db):
    match = seed_knockout_match(
        db,
        match_number=91,
        home_code="EGY",
        away_code="AUS",
        kickoff=datetime(2026, 7, 7, 19, 0, tzinfo=timezone.utc),
    )
    home = match.home_team_id
    away = match.away_team_id

    found = find_match_for_api(
        db,
        away,
        home,
        "2026-07-07T19:00:00Z",
    )
    assert found is not None
    assert found.id == match.id


def test_find_match_for_api_fuzzy_knockout_kickoff(db):
    venue = seed_venue(db)
    home = seed_team(db, fifa_code="BRA")
    away = seed_team(db, fifa_code="NOR")
    match = Match(
        match_number=91,
        stage="round_of_16",
        group_letter=None,
        home_team_id=None,
        away_team_id=None,
        venue_id=venue.id,
        kickoff_utc=datetime(2026, 7, 5, 21, 0, tzinfo=timezone.utc),
        status="upcoming",
    )
    db.add(match)
    db.commit()

    found = find_match_for_api(
        db,
        home.id,
        away.id,
        "2026-07-05T20:00:00Z",
    )
    assert found is not None
    assert found.id == match.id
    assert found.home_team_id == home.id
    assert found.away_team_id == away.id
    assert found.kickoff_utc is not None
    assert _kickoff_utc(found.kickoff_utc) == datetime(2026, 7, 5, 20, 0, tzinfo=timezone.utc)
