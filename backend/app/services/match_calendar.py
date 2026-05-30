from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def utc_bounds_for_local_day(local_day: date, tz_name: str) -> tuple[datetime, datetime]:
    """Return UTC datetimes covering all kickoffs on ``local_day`` in ``tz_name``."""
    try:
        tz = ZoneInfo(tz_name.strip())
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid timezone: {tz_name}") from exc
    start_local = datetime.combine(local_day, time.min, tzinfo=tz)
    end_local = datetime.combine(local_day, time(23, 59, 59, 999999), tzinfo=tz)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def local_date_for_utc_instant(instant: datetime, tz_name: str) -> date:
    """Map a UTC kickoff to the user's local calendar date."""
    try:
        tz = ZoneInfo(tz_name.strip())
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid timezone: {tz_name}") from exc
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    return instant.astimezone(tz).date()
