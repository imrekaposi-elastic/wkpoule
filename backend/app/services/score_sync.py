"""Fetch match scores from football-data.org and update our database."""

import logging

import httpx
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import SessionLocal
from app.models.match import Match
from app.models.team import Team
from app.services.bracket_resolver import apply_actual_knockout_teams
from app.services.match_fixture_sync import (
    advancing_team_id_from_api_score,
    find_match_for_api,
    goals_at_90_for_match,
)

logger = logging.getLogger("wkpoule.score_sync")


class FootballDataRateLimited(Exception):
    """football-data.org rejected the request due to rate limiting."""

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"rate limited; retry after {retry_after_seconds}s")


def _retry_after_seconds_from_429(response: httpx.Response) -> int:
    retry_after = response.headers.get("Retry-After")
    if retry_after and retry_after.isdigit():
        return max(1, int(retry_after))

    try:
        body = response.json()
        message = body.get("message", "")
        if "Wait " in message and " seconds" in message:
            fragment = message.split("Wait ", 1)[1].split(" seconds", 1)[0].strip()
            if fragment.isdigit():
                return max(1, int(fragment))
    except Exception:
        pass

    return 60

STATUS_RANK = {
    "upcoming": 0,
    "in_progress": 1,
    "completed": 2,
}

API_STATUS_MAP = {
    "SCHEDULED": "upcoming",
    "TIMED": "upcoming",
    "IN_PLAY": "in_progress",
    "PAUSED": "in_progress",
    "EXTRA_TIME": "in_progress",
    "PENALTY_SHOOTOUT": "in_progress",
    "FINISHED": "completed",
    "SUSPENDED": "in_progress",
    "POSTPONED": "upcoming",
    "CANCELLED": "upcoming",
    "AWARDED": "completed",
}


def resolve_sync_status(api_status: str, current_status: str) -> tuple[str, bool]:
    """Map football-data.org status to our status without downgrading.

    Returns (status_to_apply, ignored_downgrade).
    """
    mapped = API_STATUS_MAP.get(api_status)
    if mapped is None:
        return current_status, False

    current_rank = STATUS_RANK.get(current_status, 0)
    mapped_rank = STATUS_RANK.get(mapped, 0)
    if mapped_rank < current_rank:
        return current_status, True
    return mapped, False


def _resolve_winner_team_id_for_match(
    match: Match,
    api_home_id: int,
    api_away_id: int,
    home_goals: int,
    away_goals: int,
    score: dict,
) -> int | None:
    if home_goals > away_goals:
        return match.home_team_id or api_home_id
    if away_goals > home_goals:
        return match.away_team_id or api_away_id
    return advancing_team_id_from_api_score(score, api_home_id, api_away_id)


def _apply_winner_only_when_admin_overridden(
    match: Match,
    score: dict,
    api_home_id: int,
    api_away_id: int,
    *,
    our_status: str,
) -> bool:
    """Fill missing winner_team_id on admin-locked draws without touching scores."""
    if our_status != "completed":
        return False
    if match.home_score is None or match.away_score is None:
        return False
    if match.home_score != match.away_score or match.winner_team_id is not None:
        return False

    home_goals, away_goals = goals_at_90_for_match(
        match, api_home_id, api_away_id, score
    )
    if (
        home_goals is None
        or away_goals is None
        or home_goals != match.home_score
        or away_goals != match.away_score
    ):
        return False

    winner_team_id = _resolve_winner_team_id_for_match(
        match,
        api_home_id,
        api_away_id,
        home_goals,
        away_goals,
        score,
    )
    if winner_team_id is None:
        return False

    match.winner_team_id = winner_team_id
    return True


def apply_score_from_api_match(
    match: Match,
    score: dict,
    api_home_id: int,
    api_away_id: int,
    *,
    our_status: str,
) -> bool:
    """Apply 90-minute goals and advancing team from API score. Returns True if changed."""
    if match.score_overridden_by_admin:
        return _apply_winner_only_when_admin_overridden(
            match, score, api_home_id, api_away_id, our_status=our_status
        )
    if our_status != "completed":
        return False

    home_goals, away_goals = goals_at_90_for_match(
        match, api_home_id, api_away_id, score
    )
    if home_goals is None or away_goals is None:
        return False

    changed = False
    if match.home_score != home_goals or match.away_score != away_goals:
        match.home_score = home_goals
        match.away_score = away_goals
        changed = True

    winner_team_id = _resolve_winner_team_id_for_match(
        match,
        api_home_id,
        api_away_id,
        home_goals,
        away_goals,
        score,
    )

    if winner_team_id is not None and match.winner_team_id != winner_team_id:
        match.winner_team_id = winner_team_id
        changed = True

    return changed


async def sync_scores() -> int:
    """Fetch current/finished WC matches and update local DB. Returns count of updates."""
    settings = get_settings()
    if not settings.football_data_api_key:
        logger.warning("FOOTBALL_DATA_API_KEY not set — skipping score sync")
        return 0

    url = f"{settings.football_data_api_url}/competitions/WC/matches"
    headers = {"X-Auth-Token": settings.football_data_api_key}
    # Fetch all fixtures in one call. Status filters omit EXTRA_TIME / PENALTY_SHOOTOUT
    # rows while a knockout match is still in progress.

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        logger.info(
            "football-data.org API call",
            extra={
                "event.action": "external_api_request",
                "event.outcome": "success",
                "integration.name": "football-data",
                "url.domain": "api.football-data.org",
                "http.request.method": "GET",
                "http.response.status_code": resp.status_code,
                "football.matches_returned": len(data.get("matches", [])),
            },
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            retry_after = _retry_after_seconds_from_429(e.response)
            logger.warning(
                "football-data.org rate limited (429); retry after %ss",
                retry_after,
                extra={
                    "event.action": "external_api_request",
                    "event.outcome": "failure",
                    "integration.name": "football-data",
                    "url.domain": "api.football-data.org",
                    "http.request.method": "GET",
                    "http.response.status_code": 429,
                },
            )
            raise FootballDataRateLimited(retry_after) from e
        logger.error(
            "football-data.org returned %s: %s",
            e.response.status_code,
            e.response.text[:200],
            extra={
                "event.action": "external_api_request",
                "event.outcome": "failure",
                "integration.name": "football-data",
                "url.domain": "api.football-data.org",
                "http.request.method": "GET",
                "http.response.status_code": e.response.status_code,
            },
        )
        return 0
    except Exception as e:
        logger.error(
            "Failed to fetch scores: %s",
            e,
            extra={
                "event.action": "external_api_request",
                "event.outcome": "failure",
                "integration.name": "football-data",
                "url.domain": "api.football-data.org",
            },
        )
        return 0

    api_matches = data.get("matches", [])
    if not api_matches:
        logger.debug("No in-play or finished matches from API")
        return 0

    db: Session = SessionLocal()
    updates = 0
    try:
        bracket_assignments = apply_actual_knockout_teams(db)
        if bracket_assignments:
            logger.info(
                "Knockout bracket: assigned teams on %d match(es)",
                bracket_assignments,
            )
            updates += bracket_assignments

        team_by_code: dict[str, int] = {
            t.fifa_code: t.id for t in db.query(Team).all()
        }

        for am in api_matches:
            home_tla = am.get("homeTeam", {}).get("tla")
            away_tla = am.get("awayTeam", {}).get("tla")
            if not home_tla or not away_tla:
                continue

            home_id = team_by_code.get(home_tla)
            away_id = team_by_code.get(away_tla)
            if home_id is None or away_id is None:
                logger.debug("Unknown team code(s): %s / %s", home_tla, away_tla)
                continue

            utc_date = am.get("utcDate", "")
            match = find_match_for_api(db, home_id, away_id, utc_date)
            prev_home_id = match.home_team_id if match else None
            prev_away_id = match.away_team_id if match else None
            if not match:
                logger.debug("No DB match for %s vs %s", home_tla, away_tla)
                continue

            api_status = am.get("status", "")
            our_status, ignored_downgrade = resolve_sync_status(api_status, match.status)
            if ignored_downgrade:
                logger.warning(
                    "Ignoring API status downgrade for match #%d %s vs %s: "
                    "keeping %s (API=%s)",
                    match.match_number,
                    home_tla,
                    away_tla,
                    match.status,
                    api_status,
                )
            score = am.get("score", {})
            changed = False

            if (
                prev_home_id != match.home_team_id
                or prev_away_id != match.away_team_id
            ):
                logger.info(
                    "Match #%d: assigned teams %s vs %s",
                    match.match_number,
                    home_tla,
                    away_tla,
                )
                changed = True

            if our_status != match.status:
                logger.info(
                    "Match #%d %s vs %s: status %s -> %s",
                    match.match_number, home_tla, away_tla, match.status, our_status,
                )
                match.status = our_status
                changed = True

            if apply_score_from_api_match(
                match, score, home_id, away_id, our_status=our_status
            ):
                home_goals, away_goals = goals_at_90_for_match(
                    match, home_id, away_id, score
                )
                logger.info(
                    "Match #%d %s vs %s: score -> %d-%d (90 min)",
                    match.match_number, home_tla, away_tla, home_goals, away_goals,
                )
                changed = True

            if changed:
                updates += 1

        if updates > 0:
            db.commit()
            logger.info("Score sync complete: %d match(es) updated", updates)
        else:
            logger.debug("Score sync complete: no changes")
    except Exception:
        db.rollback()
        logger.exception("Error during score sync DB update")
    finally:
        db.close()

    if updates > 0:
        from app.cache.invalidation import invalidate_on_score_update
        from app.services.scoring import recalculate_points

        pts = recalculate_points()
        logger.info("Points recalculated: %d prediction(s) scored", pts)
        await invalidate_on_score_update()

    return updates
