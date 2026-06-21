"""When users may still create or change score predictions for a match.

Applies identically to group stage and knockout fixtures: locked from 30 minutes
before kickoff (UTC), while the match is in progress, and after it has started or
finished (non-``upcoming`` status).
"""

from datetime import datetime, timedelta, timezone

from app.models.match import Match

PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF = 30


def _kickoff_utc(match: Match) -> datetime:
    kickoff = match.kickoff_utc
    if kickoff.tzinfo is None:
        return kickoff.replace(tzinfo=timezone.utc)
    return kickoff


def prediction_lock_reason(match: Match) -> str | None:
    """User-facing reason predictions are locked, or None if create/update is allowed."""
    if match.status != "upcoming":
        return "Predictions are locked for this match"
    now = datetime.now(timezone.utc)
    kickoff = _kickoff_utc(match)
    cutoff = kickoff - timedelta(minutes=PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF)
    if now >= cutoff:
        return (
            "Predictions cannot be created or changed within "
            f"{PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF} minutes of kickoff "
            "or after the match has started"
        )
    return None


def match_accepts_prediction_updates(match: Match) -> bool:
    """True if predictions may be submitted or edited (server clock, UTC)."""
    return prediction_lock_reason(match) is None
