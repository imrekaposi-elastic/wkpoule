"""Shared cache read-through helpers."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from app.cache.metrics import record_cache_hit, record_cache_miss
from app.cache.service import get_cache_service

logger = logging.getLogger("wkpoule.cache")

T = TypeVar("T")


async def cached_call(
    key: str,
    ttl: int,
    model: type[T],
    compute: Callable[[], T],
) -> T:
    """Return cached JSON or compute, store, and return the fresh value."""
    cache = get_cache_service()
    hit = await cache.get_json(key, model)
    if hit is not None:
        record_cache_hit(key)
        return hit
    record_cache_miss(key)
    result = compute()
    if result is not None:
        await cache.set_json(key, result, ttl)
    return result


async def cached_call_async(
    key: str,
    ttl: int,
    model: type[T],
    compute: Callable[[], Awaitable[T]],
) -> T:
    """Like cached_call but for async compute functions."""
    cache = get_cache_service()
    hit = await cache.get_json(key, model)
    if hit is not None:
        record_cache_hit(key)
        return hit
    record_cache_miss(key)
    result = await compute()
    if result is not None:
        await cache.set_json(key, result, ttl)
    return result


def run_cache_task(coro: Awaitable[Any]) -> None:
    """Run async cache invalidation from sync route handlers (fail-open)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        try:
            asyncio.run(coro)
        except Exception as exc:
            logger.warning("cache task failed: %s", exc)
        return
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(coro)
    except Exception as exc:
        logger.warning("cache task failed: %s", exc)
