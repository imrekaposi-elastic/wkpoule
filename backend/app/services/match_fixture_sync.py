"""Resolve DB fixtures from football-data.org match payloads."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.match import Match
from app.services.scoring import resolve_winner_team_id

logger = logging.getLogger("wkpoule.match_fixture_sync")

# football-data.org kickoffs can differ from seeded fixture times by a few hours.
KICKOFF_FUZZY_TOLERANCE = timedelta(hours=6)


def parse_api_kickoff(utc_date: str) -> datetime:
    """Parse football-data.org utcDate (ISO-8601 with Z suffix)."""
    if utc_date.endswith("Z"):
        utc_date = utc_date[:-1] + "+00:00"
    dt = datetime.fromisoformat(utc_date)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _kickoff_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _goals_from_api_score_node(node: dict | None) -> tuple[int | None, int | None]:
    """Read home/away goals from a score sub-node (fullTime, regularTime, etc.)."""
    if not node:
        return None, None
    home = node.get("home")
    if home is None:
        home = node.get("homeTeam")
    away = node.get("away")
    if away is None:
        away = node.get("awayTeam")
    return home, away


def goals_at_90_from_api_score(score: dict) -> tuple[int | None, int | None]:
    """Goals after 90 minutes for tip scoring (not extra time or penalties).

    football-data.org v4 uses score/regularTime when a knockout match goes to
    extra time or penalties; score/fullTime is the running total (may include ET/pens).
    When regularTime is missing after extra time, derive it as fullTime minus extraTime.
    """
    home, away = _goals_from_api_score_node(score.get("regularTime"))
    if home is not None and away is not None:
        return home, away

    ft_home, ft_away = _goals_from_api_score_node(score.get("fullTime"))
    et_home, et_away = _goals_from_api_score_node(score.get("extraTime"))
    duration = score.get("duration")

    if (
        duration == "EXTRA_TIME"
        and ft_home is not None
        and ft_away is not None
        and et_home is not None
        and et_away is not None
    ):
        return ft_home - et_home, ft_away - et_away

    return ft_home, ft_away


def map_api_goals_to_match_orientation(
    match: Match,
    api_home_id: int,
    api_away_id: int,
    api_home_goals: int,
    api_away_goals: int,
) -> tuple[int, int]:
    """Map API home/away goals onto this match's home_team_id / away_team_id slots."""
    if match.home_team_id == api_home_id and match.away_team_id == api_away_id:
        return api_home_goals, api_away_goals
    if match.home_team_id == api_away_id and match.away_team_id == api_home_id:
        return api_away_goals, api_home_goals
    return api_home_goals, api_away_goals


def goals_at_90_for_match(
    match: Match,
    api_home_id: int,
    api_away_id: int,
    score: dict,
) -> tuple[int | None, int | None]:
    """90-minute goals aligned to the match's home/away team slots."""
    api_home_goals, api_away_goals = goals_at_90_from_api_score(score)
    if api_home_goals is None or api_away_goals is None:
        return None, None
    home_goals, away_goals = map_api_goals_to_match_orientation(
        match,
        api_home_id,
        api_away_id,
        api_home_goals,
        api_away_goals,
    )
    return home_goals, away_goals


def advancing_team_id_from_api_winner(
    winner_side: str | None,
    api_home_id: int,
    api_away_id: int,
) -> int | None:
    """Team id that advanced, from API winner relative to API home/away."""
    if winner_side == "HOME_TEAM":
        return api_home_id
    if winner_side == "AWAY_TEAM":
        return api_away_id
    return None


def advancing_team_id_from_api_score(
    score: dict,
    api_home_id: int,
    api_away_id: int,
) -> int | None:
    """Resolve the advancing team when 90-minute scores are level.

    football-data.org sometimes omits score.winner after a shootout (e.g. AUS vs EGY
    with penalties 4-4 but fullTime 3-5). Fall back to penalties, then fullTime.
    """
    stored = advancing_team_id_from_api_winner(score.get("winner"), api_home_id, api_away_id)
    if stored is not None:
        return stored

    pen_home, pen_away = _goals_from_api_score_node(score.get("penalties"))
    if pen_home is not None and pen_away is not None and pen_home != pen_away:
        return api_home_id if pen_home > pen_away else api_away_id

    reg_home, reg_away = _goals_from_api_score_node(score.get("regularTime"))
    if reg_home is None or reg_away is None:
        reg_home, reg_away = goals_at_90_from_api_score(score)
    if reg_home is None or reg_away is None:
        return None

    et_home, et_away = _goals_from_api_score_node(score.get("extraTime"))
    level_home = reg_home + (et_home or 0)
    level_away = reg_away + (et_away or 0)
    if level_home != level_away:
        return None

    ft_home, ft_away = _goals_from_api_score_node(score.get("fullTime"))
    if ft_home is None or ft_away is None or ft_home == ft_away:
        return None

    duration = score.get("duration")
    if duration in ("PENALTY_SHOOTOUT", "EXTRA_TIME") or score.get("penalties"):
        return api_home_id if ft_home > ft_away else api_away_id

    return None


def winner_team_id_from_api_score(
    home_team_id: int,
    away_team_id: int,
    home_goals: int,
    away_goals: int,
    winner_side: str | None,
    *,
    api_home_id: int | None = None,
    api_away_id: int | None = None,
) -> int | None:
    """Map 90-minute goals + API winner field to the advancing team id."""
    if home_goals > away_goals:
        return home_team_id
    if away_goals > home_goals:
        return away_team_id
    if api_home_id is not None and api_away_id is not None:
        stored = advancing_team_id_from_api_winner(winner_side, api_home_id, api_away_id)
    elif winner_side == "HOME_TEAM":
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


def _participants_match(
    match: Match,
    team_a_id: int,
    team_b_id: int,
) -> bool:
    if match.home_team_id is None or match.away_team_id is None:
        return False
    return {match.home_team_id, match.away_team_id} == {team_a_id, team_b_id}


def _can_assign_participants(
    match: Match,
    home_team_id: int,
    away_team_id: int,
) -> bool:
    if match.home_team_id is None and match.away_team_id is None:
        return True
    return _participants_match(match, home_team_id, away_team_id)


def _assign_api_participants(
    match: Match,
    home_team_id: int,
    away_team_id: int,
    kickoff: datetime,
) -> None:
    if match.home_team_id is None:
        match.home_team_id = home_team_id
    if match.away_team_id is None:
        match.away_team_id = away_team_id
    if _kickoff_utc(match.kickoff_utc) != kickoff:
        match.kickoff_utc = (
            kickoff.replace(tzinfo=None)
            if match.kickoff_utc.tzinfo is None
            else kickoff
        )


def _find_knockout_by_fuzzy_kickoff(
    db: Session,
    kickoff: datetime,
    home_team_id: int,
    away_team_id: int,
) -> Match | None:
    window_start = kickoff - KICKOFF_FUZZY_TOLERANCE
    window_end = kickoff + KICKOFF_FUZZY_TOLERANCE
    candidates = [
        candidate
        for candidate in db.query(Match).filter(Match.match_number >= 73).all()
        if window_start <= _kickoff_utc(candidate.kickoff_utc) <= window_end
    ]
    valid = [
        candidate
        for candidate in candidates
        if _can_assign_participants(candidate, home_team_id, away_team_id)
    ]
    if not valid:
        return None

    unassigned = [
        candidate
        for candidate in valid
        if candidate.home_team_id is None and candidate.away_team_id is None
    ]
    pool = unassigned if unassigned else valid
    return min(
        pool,
        key=lambda candidate: abs(
            (_kickoff_utc(candidate.kickoff_utc) - kickoff).total_seconds()
        ),
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

    match = (
        db.query(Match)
        .filter(Match.home_team_id == away_team_id, Match.away_team_id == home_team_id)
        .first()
    )
    if match:
        return match

    kickoff = parse_api_kickoff(utc_date)
    match = db.query(Match).filter(Match.kickoff_utc == kickoff).first()
    if match is None:
        match = _find_knockout_by_fuzzy_kickoff(db, kickoff, home_team_id, away_team_id)
        if match is None:
            return None
        logger.info(
            "Match #%d: fuzzy kickoff match for API %s (DB %s)",
            match.match_number,
            kickoff.isoformat(),
            match.kickoff_utc.isoformat(),
        )
    elif match.match_number < 73:
        logger.debug(
            "Kickoff match #%d is group stage but team ids differ from API",
            match.match_number,
        )
        return None

    if not _can_assign_participants(match, home_team_id, away_team_id):
        logger.warning(
            "Kickoff match #%d teams %s/%s do not match API participants",
            match.match_number,
            match.home_team_id,
            match.away_team_id,
        )
        return None

    _assign_api_participants(match, home_team_id, away_team_id, kickoff)
    return match
