"""Unit tests for CacheService."""

import fakeredis.aioredis
import pytest
from pydantic import BaseModel

from app.cache.service import CacheService


class SampleModel(BaseModel):
    name: str
    count: int


@pytest.fixture
def cache_service():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return CacheService(fake)


async def test_get_returns_none_on_miss(cache_service):
    assert await cache_service.get("missing") is None


async def test_set_and_get_round_trip(cache_service):
    assert await cache_service.set("key", "value", ttl=60) is True
    assert await cache_service.get("key") == "value"


async def test_delete_removes_key(cache_service):
    await cache_service.set("key", "value", ttl=60)
    assert await cache_service.delete("key") is True
    assert await cache_service.get("key") is None


async def test_set_json_and_get_json(cache_service):
    model = SampleModel(name="test", count=3)
    assert await cache_service.set_json("json-key", model, ttl=60) is True
    loaded = await cache_service.get_json("json-key", SampleModel)
    assert loaded == model


async def test_fail_open_when_redis_unavailable():
    service = CacheService(None)
    assert await service.get("key") is None
    assert await service.set("key", "value", ttl=60) is False
    assert await service.delete("key") is False
    assert await service.delete_pattern("wkpoule:*") == 0


async def test_delete_pattern(cache_service):
    await cache_service.set("wkpoule:rankings:page=1:size=20", "a", ttl=60)
    await cache_service.set("wkpoule:rankings:page=2:size=20", "b", ttl=60)
    await cache_service.set("wkpoule:teams:list", "c", ttl=60)
    deleted = await cache_service.delete_pattern("wkpoule:rankings:*")
    assert deleted == 2
    assert await cache_service.get("wkpoule:teams:list") == "c"
