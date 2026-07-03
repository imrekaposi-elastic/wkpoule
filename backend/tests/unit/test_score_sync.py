"""Unit tests for football-data.org score sync status handling."""

from app.services.score_sync import apply_score_from_api_match, resolve_sync_status
from tests.seed_fixtures import seed_knockout_match


def test_resolve_sync_status_maps_finished_to_completed():
    status, ignored = resolve_sync_status("FINISHED", "in_progress")
    assert status == "completed"
    assert ignored is False


def test_resolve_sync_status_maps_extra_time_to_in_progress():
    status, ignored = resolve_sync_status("EXTRA_TIME", "upcoming")
    assert status == "in_progress"
    assert ignored is False


def test_resolve_sync_status_blocks_completed_to_in_progress():
    status, ignored = resolve_sync_status("IN_PLAY", "completed")
    assert status == "completed"
    assert ignored is True


def test_resolve_sync_status_blocks_completed_to_upcoming():
    status, ignored = resolve_sync_status("TIMED", "completed")
    assert status == "completed"
    assert ignored is True


def test_resolve_sync_status_unknown_api_status_keeps_current():
    status, ignored = resolve_sync_status("WEIRD_STATUS", "completed")
    assert status == "completed"
    assert ignored is False


def test_apply_score_from_api_match_uses_regular_time_for_knockout(db):
    match = seed_knockout_match(db, match_number=201)
    home_id = match.home_team_id
    away_id = match.away_team_id
    score = {
        "winner": "HOME_TEAM",
        "duration": "PENALTY_SHOOTOUT",
        "fullTime": {"home": 7, "away": 6},
        "regularTime": {"home": 1, "away": 1},
    }

    changed = apply_score_from_api_match(
        match, score, home_id, away_id, our_status="completed"
    )

    assert changed is True
    assert match.home_score == 1
    assert match.away_score == 1
    assert match.winner_team_id == home_id


def test_apply_score_from_api_match_skips_admin_override(db):
    match = seed_knockout_match(db, match_number=202)
    match.home_score = 2
    match.away_score = 2
    match.winner_team_id = match.away_team_id
    match.score_overridden_by_admin = True
    db.commit()

    score = {
        "winner": "HOME_TEAM",
        "duration": "PENALTY_SHOOTOUT",
        "fullTime": {"home": 7, "away": 6},
        "regularTime": {"home": 1, "away": 1},
    }

    changed = apply_score_from_api_match(
        match,
        score,
        match.home_team_id,
        match.away_team_id,
        our_status="completed",
    )

    assert changed is False
    assert match.home_score == 2
    assert match.away_score == 2
    assert match.winner_team_id == match.away_team_id


def test_apply_score_fills_missing_winner_when_admin_overridden(db):
    match = seed_knockout_match(db, match_number=203)
    egypt_id = match.home_team_id
    australia_id = match.away_team_id
    match.home_score = 1
    match.away_score = 1
    match.winner_team_id = None
    match.score_overridden_by_admin = True
    db.commit()

    score = {
        "winner": "HOME_TEAM",
        "duration": "PENALTY_SHOOTOUT",
        "regularTime": {"home": 1, "away": 1},
    }

    changed = apply_score_from_api_match(
        match,
        score,
        egypt_id,
        australia_id,
        our_status="completed",
    )

    assert changed is True
    assert match.winner_team_id == egypt_id


def test_apply_score_swapped_db_teams_sets_api_winner_team_id(db):
    match = seed_knockout_match(db, match_number=204, home_code="EGY", away_code="AUS")
    egypt_id = match.home_team_id
    australia_id = match.away_team_id
    score = {
        "winner": "AWAY_TEAM",
        "duration": "PENALTY_SHOOTOUT",
        "regularTime": {"home": 1, "away": 1},
    }

    changed = apply_score_from_api_match(
        match,
        score,
        australia_id,
        egypt_id,
        our_status="completed",
    )

    assert changed is True
    assert match.home_score == 1
    assert match.away_score == 1
    assert match.winner_team_id == egypt_id
