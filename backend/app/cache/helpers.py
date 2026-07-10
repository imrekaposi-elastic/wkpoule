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

_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Store the FastAPI/uvicorn loop so sync routes can schedule cache tasks on it."""
    global _main_loop
    _main_loop = loop


def reset_main_event_loop() -> None:
    global _main_loop
    _main_loop = None


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


def _log_cache_task_result(future: asyncio.Future[Any]) -> None:
    try:
        future.result()
    except Exception as exc:
        logger.warning("cache task failed: %s", exc)


def run_cache_task(coro: Awaitable[Any]) -> None:
    """Run async cache invalidation from sync route handlers (fail-open).

    Sync FastAPI routes run in a thread pool without an event loop. The shared
    Redis client is bound to the uvicorn loop, so we must schedule work there
    instead of calling asyncio.run() in the worker thread.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        try:
            task = loop.create_task(coro)
            task.add_done_callback(_log_cache_task_result)
        except Exception as exc:
            logger.warning("cache task failed: %s", exc)
        return

    app_loop = _main_loop
    if app_loop is not None and app_loop.is_running():
        try:
            future = asyncio.run_coroutine_threadsafe(coro, app_loop)
            future.add_done_callback(_log_cache_task_result)
        except Exception as exc:
            logger.warning("cache task failed: %s", exc)
        return

    try:
        asyncio.run(coro)
    except Exception as exc:
        logger.warning("cache task failed: %s", exc)
