"""Unit tests for match prediction lock window."""

from datetime import datetime, timedelta, timezone

from app.models.match import Match
from app.services.prediction_lock import (
    PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF,
    match_accepts_prediction_updates,
)


def _upcoming_match(kickoff: datetime) -> Match:
    return Match(
        id=1,
        match_number=1,
        stage="group",
        group_letter="A",
        venue_id=1,
        kickoff_utc=kickoff,
        status="upcoming",
    )


def test_accepts_updates_more_than_lock_window_before_kickoff():
    kickoff = datetime.now(timezone.utc) + timedelta(hours=2)
    match = _upcoming_match(kickoff)

    assert match_accepts_prediction_updates(match) is True


def test_rejects_updates_within_lock_window():
    kickoff = datetime.now(timezone.utc) + timedelta(
        minutes=PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF - 1
    )
    match = _upcoming_match(kickoff)

    assert match_accepts_prediction_updates(match) is False


def test_rejects_non_upcoming_matches():
    kickoff = datetime.now(timezone.utc) + timedelta(days=2)
    match = _upcoming_match(kickoff)
    match.status = "completed"

    assert match_accepts_prediction_updates(match) is False


def test_naive_kickoff_treated_as_utc():
    kickoff = datetime.utcnow() + timedelta(hours=2)
    match = _upcoming_match(kickoff)

    assert match_accepts_prediction_updates(match) is True
