"""When users may still create or change score predictions for a match."""

from datetime import datetime, timedelta, timezone

from app.models.match import Match

PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF = 30


def match_accepts_prediction_updates(match: Match) -> bool:
    """True if predictions may be submitted or edited (server clock, UTC)."""
    if match.status != "upcoming":
        return False
    now = datetime.now(timezone.utc)
    kickoff = match.kickoff_utc
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)
    cutoff = kickoff - timedelta(minutes=PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF)
    return now < cutoff
