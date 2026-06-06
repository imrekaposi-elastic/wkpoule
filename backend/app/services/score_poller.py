"""Background task that periodically syncs match scores from football-data.org."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, time, timedelta, timezone

from app.config import get_settings

logger = logging.getLogger("wkpoule.score_poller")

MIN_SYNC_INTERVAL = timedelta(hours=2)
MAX_SYNCS_PER_DAY = 10

_task: asyncio.Task | None = None
_last_sync_at: datetime | None = None
_syncs_on_date: date | None = None
_sync_count_today = 0


def start_polling() -> None:
    global _task
    settings = get_settings()
    if not settings.football_data_api_key:
        logger.warning("FOOTBALL_DATA_API_KEY not set — score poller disabled")
        return
    _task = asyncio.create_task(_poll_loop())
    logger.info(
        "Score poller started (max %d syncs/day, min %dh between syncs)",
        MAX_SYNCS_PER_DAY,
        int(MIN_SYNC_INTERVAL.total_seconds() // 3600),
    )


def stop_polling() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
        logger.info("Score poller stopped")
    _task = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _reset_daily_count_if_needed(now: datetime) -> None:
    global _syncs_on_date, _sync_count_today
    today = now.date()
    if _syncs_on_date != today:
        _syncs_on_date = today
        _sync_count_today = 0


def _daily_limit_reached(now: datetime) -> bool:
    _reset_daily_count_if_needed(now)
    return _sync_count_today >= MAX_SYNCS_PER_DAY


def _record_sync(now: datetime) -> None:
    global _last_sync_at, _sync_count_today
    _reset_daily_count_if_needed(now)
    _sync_count_today += 1
    _last_sync_at = now


def seconds_until_next_sync(
    now: datetime,
    *,
    last_sync_at: datetime | None = None,
    syncs_on_date: date | None = None,
    sync_count_today: int = 0,
) -> int:
    """Seconds to wait before the next score API call is allowed."""
    today = now.date()
    count_today = sync_count_today if syncs_on_date == today else 0

    if count_today >= MAX_SYNCS_PER_DAY:
        next_day = datetime.combine(today + timedelta(days=1), time.min, tzinfo=timezone.utc)
        return max(1, int((next_day - now).total_seconds()))

    if last_sync_at is None:
        return 0

    elapsed = now - last_sync_at
    remaining = MIN_SYNC_INTERVAL - elapsed
    return max(0, int(remaining.total_seconds()))


async def _poll_loop() -> None:
    from app.services.score_sync import sync_scores

    global _last_sync_at, _syncs_on_date, _sync_count_today

    while True:
        now = _utc_now()
        wait = seconds_until_next_sync(
            now,
            last_sync_at=_last_sync_at,
            syncs_on_date=_syncs_on_date,
            sync_count_today=_sync_count_today,
        )
        if wait > 0:
            logger.debug("Next score sync in %ds", wait)
            await asyncio.sleep(wait)

        now = _utc_now()
        if _daily_limit_reached(now):
            logger.info("Daily score sync limit reached (%d/%d)", _sync_count_today, MAX_SYNCS_PER_DAY)
            continue

        try:
            updated = await sync_scores()
            _record_sync(now)
            if updated:
                logger.info("Synced %d score update(s)", updated)
            else:
                logger.debug("Score sync complete: no changes")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Score sync failed — will retry after interval")
