"""Unit tests for Redis client lifecycle."""

from unittest.mock import AsyncMock, patch

import fakeredis.aioredis
import pytest

from app.cache import redis_client
from app.cache.redis_client import close_redis, get_redis, init_redis, redis_ping


@pytest.fixture(autouse=True)
async def reset_redis_state():
    await close_redis()
    redis_client._instrumented = False
    yield
    await close_redis()
    redis_client._instrumented = False


async def test_init_redis_connects_with_fakeredis():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with patch("app.cache.redis_client.aioredis.Redis", return_value=fake):
        with patch("app.cache.redis_client.aioredis.ConnectionPool.from_url"):
            await init_redis()

    assert get_redis() is fake
    assert await redis_ping() is True


async def test_init_redis_fail_open_on_connection_error():
    broken = AsyncMock()
    broken.ping.side_effect = ConnectionError("refused")
    broken.aclose = AsyncMock()

    with patch("app.cache.redis_client.aioredis.Redis", return_value=broken):
        with patch("app.cache.redis_client.aioredis.ConnectionPool.from_url"):
            await init_redis()

    assert get_redis() is None
    assert await redis_ping() is False


async def test_close_redis_clears_client():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    redis_client._redis = fake
    await close_redis()
    assert get_redis() is None
