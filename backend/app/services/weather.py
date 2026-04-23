import httpx
from datetime import datetime, timezone, timedelta

from app.config import get_settings

_cache: dict[int, float] = {}

HISTORICAL_AVERAGES: dict[str, float] = {
    "Mexico City": 18.0,
    "Guadalajara": 25.0,
    "Monterrey": 30.0,
    "New York": 27.0,
    "East Rutherford": 27.0,
    "Los Angeles": 25.0,
    "Inglewood": 25.0,
    "Pasadena": 28.0,
    "Miami": 30.0,
    "Miami Gardens": 30.0,
    "Houston": 32.0,
    "Dallas": 33.0,
    "Arlington": 33.0,
    "Atlanta": 29.0,
    "Philadelphia": 28.0,
    "Seattle": 20.0,
    "San Francisco": 18.0,
    "Santa Clara": 22.0,
    "Boston": 25.0,
    "Foxborough": 25.0,
    "Kansas City": 29.0,
    "Toronto": 23.0,
    "Vancouver": 19.0,
}


async def get_match_temperature(match_id: int, city: str, kickoff: datetime) -> float | None:
    if match_id in _cache:
        return _cache[match_id]

    settings = get_settings()
    if settings.weather_api_key:
        temp = await _fetch_from_api(city, kickoff, settings)
        if temp is not None:
            _cache[match_id] = temp
            return temp

    temp = HISTORICAL_AVERAGES.get(city)
    if temp is not None:
        _cache[match_id] = temp
    return temp


async def _fetch_from_api(city: str, kickoff: datetime, settings) -> float | None:
    now = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            if kickoff <= now + timedelta(days=14):
                resp = await client.get(
                    f"{settings.weather_api_url}/forecast.json",
                    params={"key": settings.weather_api_key, "q": city, "dt": kickoff.strftime("%Y-%m-%d")},
                )
            else:
                resp = await client.get(
                    f"{settings.weather_api_url}/history.json",
                    params={"key": settings.weather_api_key, "q": city, "dt": kickoff.strftime("%Y-%m-%d")},
                )
            if resp.status_code == 200:
                data = resp.json()
                day = data.get("forecast", {}).get("forecastday", [{}])[0]
                return day.get("day", {}).get("avgtemp_c")
    except Exception:
        pass
    return None
