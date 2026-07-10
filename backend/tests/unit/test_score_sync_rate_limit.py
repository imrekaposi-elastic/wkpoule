"""Unit tests for football-data.org 429 handling."""

import httpx
import pytest

from app.services.score_sync import (
    FootballDataRateLimited,
    _retry_after_seconds_from_429,
)


def test_retry_after_seconds_from_message_body():
    response = httpx.Response(
        429,
        json={"message": "You reached your request limit. Wait 28 seconds.", "errorCode": 429},
    )
    assert _retry_after_seconds_from_429(response) == 28


def test_retry_after_seconds_from_header():
    response = httpx.Response(429, headers={"Retry-After": "45"})
    assert _retry_after_seconds_from_429(response) == 45


def test_football_data_rate_limited_carries_retry_seconds():
    exc = FootballDataRateLimited(30)
    assert exc.retry_after_seconds == 30
