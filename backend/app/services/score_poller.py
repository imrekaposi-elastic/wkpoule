"""Background task that periodically syncs match scores from football-data.org."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.database import SessionLocal
from app.models.match import Match

logger = logging.getLogger("wkpoule.score_poller")

POLL_FAST = 120      # seconds between polls when matches are active
POLL_SLOW = 1800     # seconds between polls on quiet days
MATCH_WINDOW = 3     # hours before/after a kickoff to consider "active"

_task: asyncio.Task | None = None


def start_polling() -> None:
    global _task
    settings = get_settings()
    if not settings.football_data_api_key:
        logger.warning("FOOTBALL_DATA_API_KEY not set — score poller disabled")
        return
    _task = asyncio.create_task(_poll_loop())
    logger.info("Score poller started")


def stop_polling() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
        logger.info("Score poller stopped")
    _task = None


async def _poll_loop() -> None:
    from app.services.score_sync import sync_scores

    while True:
        interval = _pick_interval()
        logger.debug("Next score sync in %ds", interval)
        await asyncio.sleep(interval)
        try:
            updated = await sync_scores()
            if updated:
                logger.info("Synced %d score update(s)", updated)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Score sync failed — will retry next cycle")


def _pick_interval() -> int:
    """Return a short interval if matches are happening today, otherwise long."""
    now = datetime.now(timezone.utc)
    window = timedelta(hours=MATCH_WINDOW)

    db = SessionLocal()
    try:
        active = (
            db.query(Match)
            .filter(
                Match.kickoff_utc >= now - window,
                Match.kickoff_utc <= now + window,
                Match.status.in_(["upcoming", "in_progress"]),
            )
            .count()
        )
    finally:
        db.close()

    if active > 0:
        logger.debug("%d match(es) in active window — using fast poll", active)
        return POLL_FAST
    return POLL_SLOW
