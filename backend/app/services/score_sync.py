"""Fetch match scores from football-data.org and update our database."""

import logging

import httpx
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import SessionLocal
from app.models.match import Match
from app.models.team import Team

logger = logging.getLogger("wkpoule.score_sync")

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


async def sync_scores() -> int:
    """Fetch current/finished WC matches and update local DB. Returns count of updates."""
    settings = get_settings()
    if not settings.football_data_api_key:
        logger.warning("FOOTBALL_DATA_API_KEY not set — skipping score sync")
        return 0

    url = f"{settings.football_data_api_url}/competitions/WC/matches"
    headers = {"X-Auth-Token": settings.football_data_api_key}
    # AWARDED is a match status in responses but not a valid ?status= filter value on v4.
    params = {"status": "LIVE,IN_PLAY,PAUSED,FINISHED"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers, params=params)
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

            match = (
                db.query(Match)
                .filter(Match.home_team_id == home_id, Match.away_team_id == away_id)
                .first()
            )
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
            # fullTime = end of regular time (90 min); extra time / pens are separate fields.
            ft = score.get("fullTime", {})
            home_goals = ft.get("home")
            away_goals = ft.get("away")
            winner_side = score.get("winner")

            changed = False

            if our_status != match.status:
                logger.info(
                    "Match #%d %s vs %s: status %s -> %s",
                    match.match_number, home_tla, away_tla, match.status, our_status,
                )
                match.status = our_status
                changed = True

            if (
                our_status == "completed"
                and home_goals is not None
                and away_goals is not None
            ):
                if match.home_score != home_goals or match.away_score != away_goals:
                    logger.info(
                        "Match #%d %s vs %s: score %s-%s -> %d-%d",
                        match.match_number, home_tla, away_tla,
                        match.home_score, match.away_score, home_goals, away_goals,
                    )
                    match.home_score = home_goals
                    match.away_score = away_goals
                    changed = True

                if home_goals > away_goals:
                    winner_team_id = home_id
                elif away_goals > home_goals:
                    winner_team_id = away_id
                elif winner_side == "HOME_TEAM":
                    winner_team_id = home_id
                elif winner_side == "AWAY_TEAM":
                    winner_team_id = away_id
                else:
                    winner_team_id = None

                if match.winner_team_id != winner_team_id:
                    match.winner_team_id = winner_team_id
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
