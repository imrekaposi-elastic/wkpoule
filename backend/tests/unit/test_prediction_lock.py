"""Unit tests for match prediction lock window."""

import pytest

from datetime import datetime, timedelta, timezone

from app.models.match import Match
from app.services.prediction_lock import (
    PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF,
    match_accepts_prediction_updates,
    prediction_lock_reason,
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
    assert prediction_lock_reason(match) == "Predictions are locked for this match"


def test_rejects_in_progress_matches():
    kickoff = datetime.now(timezone.utc) + timedelta(hours=1)
    match = _upcoming_match(kickoff)
    match.status = "in_progress"

    assert match_accepts_prediction_updates(match) is False


def test_rejects_live_matches():
    kickoff = datetime.now(timezone.utc) + timedelta(hours=1)
    match = _upcoming_match(kickoff)
    match.status = "live"

    assert match_accepts_prediction_updates(match) is False


@pytest.mark.parametrize(
    "stage",
    [
        "group",
        "round_of_32",
        "round_of_16",
        "quarter_final",
        "semi_final",
        "final",
    ],
)
def test_knockout_and_group_share_same_lock_window(stage):
    kickoff = datetime.now(timezone.utc) + timedelta(
        minutes=PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF - 1
    )
    match = _upcoming_match(kickoff)
    match.stage = stage

    assert match_accepts_prediction_updates(match) is False


def test_rejects_after_kickoff_even_if_status_still_upcoming():
    kickoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    match = _upcoming_match(kickoff)

    assert match_accepts_prediction_updates(match) is False
    assert prediction_lock_reason(match) is not None


def test_naive_kickoff_treated_as_utc():
    kickoff = datetime.utcnow() + timedelta(hours=2)
    match = _upcoming_match(kickoff)

    assert match_accepts_prediction_updates(match) is True
