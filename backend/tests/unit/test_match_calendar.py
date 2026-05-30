from datetime import date, datetime, timezone

import pytest

from app.services.match_calendar import utc_bounds_for_local_day


def test_utc_bounds_for_local_day_europe_amsterdam():
    start, end = utc_bounds_for_local_day(date(2026, 6, 11), "Europe/Amsterdam")
    assert start == datetime(2026, 6, 10, 22, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 6, 11, 21, 59, 59, 999999, tzinfo=timezone.utc)


def test_utc_bounds_for_local_day_utc():
    start, end = utc_bounds_for_local_day(date(2026, 6, 11), "UTC")
    assert start == datetime(2026, 6, 11, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 6, 11, 23, 59, 59, 999999, tzinfo=timezone.utc)


def test_utc_bounds_rejects_invalid_timezone():
    with pytest.raises(ValueError, match="Invalid timezone"):
        utc_bounds_for_local_day(date(2026, 6, 11), "Not/A/Timezone")
