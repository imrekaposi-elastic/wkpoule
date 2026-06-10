"""Async Redis client with connection pooling and fail-open behaviour."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import redis.asyncio as aioredis
from opentelemetry.instrumentation.redis import RedisInstrumentor

from app.config import get_settings

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger("wkpoule.cache")

_redis: Redis | None = None
_instrumented = False


def _ensure_instrumented() -> None:
    global _instrumented
    if not _instrumented:
        RedisInstrumentor().instrument()
        _instrumented = True


async def init_redis() -> None:
    """Create the shared Redis connection pool. Fail-open if Redis is unreachable."""
    global _redis
    if _redis is not None:
        return

    _ensure_instrumented()
    settings = get_settings()
    pool = aioredis.ConnectionPool.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        decode_responses=True,
    )
    client = aioredis.Redis(connection_pool=pool)
    try:
        await client.ping()
        _redis = client
        logger.info("Redis connected", extra={"event.action": "redis_connect", "event.outcome": "success"})
    except Exception as exc:
        await client.aclose()
        logger.warning(
            "Redis unavailable at startup (fail-open): %s",
            exc,
            extra={"event.action": "redis_connect", "event.outcome": "failure"},
        )


async def close_redis() -> None:
    """Close the shared Redis client and connection pool."""
    global _redis
    if _redis is None:
        return
    try:
        await _redis.aclose()
    except Exception as exc:
        logger.warning("Error closing Redis client: %s", exc)
    finally:
        _redis = None


def get_redis() -> Redis | None:
    return _redis


async def redis_ping() -> bool:
    """Return True when Redis responds to PING."""
    if _redis is None:
        return False
    try:
        return bool(await _redis.ping())
    except Exception as exc:
        logger.warning("Redis ping failed: %s", exc)
        return False
