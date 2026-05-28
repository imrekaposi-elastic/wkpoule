"""Unit tests for knockout advance-on-draw validation."""

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.match import Match
from app.services.prediction_advance import validate_advance_team_for_prediction


def _knockout_match(home_id: int = 1, away_id: int = 2) -> Match:
    return Match(
        id=10,
        match_number=89,
        stage="round_of_16",
        group_letter=None,
        venue_id=1,
        kickoff_utc=datetime(2026, 7, 4, 17, tzinfo=timezone.utc),
        status="upcoming",
        home_team_id=home_id,
        away_team_id=away_id,
    )


def test_group_match_rejects_advance_team():
    match = _knockout_match()
    match.stage = "group"
    match.group_letter = "A"

    with pytest.raises(HTTPException) as exc:
        validate_advance_team_for_prediction(match, 1, 1, 1)

    assert exc.value.status_code == 400


def test_knockout_non_draw_clears_advance():
    match = _knockout_match()
    assert validate_advance_team_for_prediction(match, 2, 1, None) is None

    with pytest.raises(HTTPException):
        validate_advance_team_for_prediction(match, 2, 1, 1)


def test_knockout_draw_requires_advance_team():
    match = _knockout_match()

    with pytest.raises(HTTPException) as exc:
        validate_advance_team_for_prediction(match, 1, 1, None)
    assert "advance" in exc.value.detail.lower()

    assert validate_advance_team_for_prediction(match, 1, 1, 1) == 1
    assert validate_advance_team_for_prediction(match, 1, 1, 2) == 2

    with pytest.raises(HTTPException):
        validate_advance_team_for_prediction(match, 1, 1, 99)
