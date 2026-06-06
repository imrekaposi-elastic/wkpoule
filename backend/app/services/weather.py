import httpx
from datetime import date, datetime, timezone, timedelta
import logging

from app.config import get_settings

logger = logging.getLogger("wkpoule.weather")

_match_cache: dict[int, float] = {}
_city_date_cache: dict[tuple[str, str], float] = {}
_api_calls_on_date: date | None = None
_api_calls_today = 0

# Safety cap so a cold cache + heavy browsing cannot exhaust the quota in one day.
WEATHER_API_MAX_CALLS_PER_DAY = 50
FORECAST_HORIZON_DAYS = 14

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


def _kickoff_date_key(kickoff: datetime) -> str:
    return kickoff.date().isoformat()


def _fallback_temperature(city: str) -> float | None:
    return HISTORICAL_AVERAGES.get(city)


def _weather_api_budget_remaining(now: datetime) -> bool:
    global _api_calls_on_date, _api_calls_today
    today = now.date()
    if _api_calls_on_date != today:
        _api_calls_on_date = today
        _api_calls_today = 0
    return _api_calls_today < WEATHER_API_MAX_CALLS_PER_DAY


def _record_weather_api_call(now: datetime) -> None:
    global _api_calls_on_date, _api_calls_today
    today = now.date()
    if _api_calls_on_date != today:
        _api_calls_on_date = today
        _api_calls_today = 0
    _api_calls_today += 1


async def get_match_temperature(match_id: int, city: str, kickoff: datetime) -> float | None:
    if match_id in _match_cache:
        return _match_cache[match_id]

    city_date = (city, _kickoff_date_key(kickoff))
    if city_date in _city_date_cache:
        temp = _city_date_cache[city_date]
        _match_cache[match_id] = temp
        return temp

    settings = get_settings()
    now = datetime.now(timezone.utc)
    temp: float | None = None

    if settings.weather_api_key and _weather_api_budget_remaining(now):
        # Only use the forecast endpoint (within 14 days). Skip paid/history lookups.
        if kickoff <= now + timedelta(days=FORECAST_HORIZON_DAYS):
            temp = await _fetch_forecast(city, kickoff, settings)
            if temp is not None:
                _record_weather_api_call(now)

    if temp is None:
        temp = _fallback_temperature(city)

    if temp is not None:
        _city_date_cache[city_date] = temp
        _match_cache[match_id] = temp
    return temp


async def _fetch_forecast(city: str, kickoff: datetime, settings) -> float | None:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{settings.weather_api_url}/forecast.json",
                params={
                    "key": settings.weather_api_key,
                    "q": city,
                    "dt": kickoff.strftime("%Y-%m-%d"),
                },
            )
            logger.info(
                "weather API call",
                extra={
                    "event.action": "external_api_request",
                    "event.outcome": "success" if resp.status_code == 200 else "failure",
                    "integration.name": "weatherapi",
                    "url.domain": "api.weatherapi.com",
                    "http.request.method": "GET",
                    "http.response.status_code": resp.status_code,
                    "weather.city": city,
                    "weather.date": kickoff.strftime("%Y-%m-%d"),
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                day = data.get("forecast", {}).get("forecastday", [{}])[0]
                return day.get("day", {}).get("avgtemp_c")
    except Exception:
        logger.exception(
            "weather API call failed",
            extra={
                "event.action": "external_api_request",
                "event.outcome": "failure",
                "integration.name": "weatherapi",
                "url.domain": "api.weatherapi.com",
                "weather.city": city,
            },
        )
    return None
