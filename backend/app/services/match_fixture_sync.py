"""Resolve DB fixtures from football-data.org match payloads."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.match import Match
from app.services.scoring import resolve_winner_team_id

logger = logging.getLogger("wkpoule.match_fixture_sync")


def parse_api_kickoff(utc_date: str) -> datetime:
    """Parse football-data.org utcDate (ISO-8601 with Z suffix)."""
    if utc_date.endswith("Z"):
        utc_date = utc_date[:-1] + "+00:00"
    dt = datetime.fromisoformat(utc_date)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def winner_team_id_from_api_score(
    home_team_id: int,
    away_team_id: int,
    home_goals: int,
    away_goals: int,
    winner_side: str | None,
) -> int | None:
    """Map 90-minute goals + API winner field to the advancing team id."""
    if winner_side == "HOME_TEAM":
        stored = home_team_id
    elif winner_side == "AWAY_TEAM":
        stored = away_team_id
    else:
        stored = None
    return resolve_winner_team_id(
        home_team_id,
        away_team_id,
        home_goals,
        away_goals,
        stored,
    )


def find_match_for_api(
    db: Session,
    home_team_id: int,
    away_team_id: int,
    utc_date: str,
) -> Match | None:
    """Find a fixture by participants, or by kickoff for unassigned knockout slots."""
    match = (
        db.query(Match)
        .filter(Match.home_team_id == home_team_id, Match.away_team_id == away_team_id)
        .first()
    )
    if match:
        return match

    kickoff = parse_api_kickoff(utc_date)
    match = db.query(Match).filter(Match.kickoff_utc == kickoff).first()
    if match is None:
        return None

    if match.match_number < 73:
        logger.debug(
            "Kickoff match #%d is group stage but team ids differ from API",
            match.match_number,
        )
        return None

    if match.home_team_id is None:
        match.home_team_id = home_team_id
    if match.away_team_id is None:
        match.away_team_id = away_team_id

    if match.home_team_id != home_team_id or match.away_team_id != away_team_id:
        logger.warning(
            "Kickoff match #%d teams %s/%s do not match API participants",
            match.match_number,
            match.home_team_id,
            match.away_team_id,
        )
        return None

    return match
