"""Unit tests for cached router read-through behaviour."""

import asyncio
import threading

import fakeredis.aioredis
import pytest
from pydantic import BaseModel

from app.cache.helpers import cached_call, run_cache_task, set_main_event_loop
from app.cache.service import CacheService


class Item(BaseModel):
    value: int


@pytest.fixture
def cache_service():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return CacheService(fake)


async def test_cached_call_stores_and_reuses_value(monkeypatch, cache_service):
    monkeypatch.setattr("app.cache.helpers.get_cache_service", lambda: cache_service)
    calls = {"count": 0}

    def compute() -> Item:
        calls["count"] += 1
        return Item(value=42)

    first = await cached_call("wkpoule:test:item", 60, Item, compute)
    second = await cached_call("wkpoule:test:item", 60, Item, compute)

    assert first.value == 42
    assert second.value == 42
    assert calls["count"] == 1


async def test_cached_call_skips_caching_none(monkeypatch, cache_service):
    monkeypatch.setattr("app.cache.helpers.get_cache_service", lambda: cache_service)
    calls = {"count": 0}

    def compute() -> Item | None:
        calls["count"] += 1
        return None

    await cached_call("wkpoule:test:none", 60, Item | None, compute)
    await cached_call("wkpoule:test:none", 60, Item | None, compute)

    assert calls["count"] == 2


async def test_run_cache_task_from_sync_thread_uses_main_loop():
    set_main_event_loop(asyncio.get_running_loop())
    done = threading.Event()
    seen: list[int] = []

    async def mark_done() -> None:
        seen.append(1)

    def sync_worker() -> None:
        run_cache_task(mark_done())
        done.set()

    worker = threading.Thread(target=sync_worker)
    worker.start()
    worker.join(timeout=2)
    assert done.is_set()

    for _ in range(50):
        if seen:
            break
        await asyncio.sleep(0.01)

    assert seen == [1]
