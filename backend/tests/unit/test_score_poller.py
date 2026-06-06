from datetime import datetime, timezone

from app.services.score_poller import (
    MAX_SYNCS_PER_DAY,
    seconds_until_next_sync,
)


def test_first_sync_can_run_immediately():
    now = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    assert seconds_until_next_sync(now, last_sync_at=None) == 0


def test_second_sync_waits_two_hours():
    now = datetime(2026, 6, 5, 13, 0, tzinfo=timezone.utc)
    last = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    assert seconds_until_next_sync(now, last_sync_at=last) == 3600


def test_daily_limit_waits_until_next_utc_day():
    now = datetime(2026, 6, 5, 22, 0, tzinfo=timezone.utc)
    wait = seconds_until_next_sync(
        now,
        last_sync_at=datetime(2026, 6, 5, 20, 0, tzinfo=timezone.utc),
        syncs_on_date=now.date(),
        sync_count_today=MAX_SYNCS_PER_DAY,
    )
    assert wait == 2 * 3600
