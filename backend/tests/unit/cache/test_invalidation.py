"""Unit tests for cache invalidation helpers."""

import fakeredis.aioredis
import pytest

from app.cache.invalidation import (
    invalidate_match,
    invalidate_on_prediction,
    invalidate_on_score_update,
    invalidate_rankings,
    invalidate_subgroup,
    invalidate_user_virtual_groups,
    invalidate_virtual_groups,
)
from app.cache.keys import CacheKeys
from app.cache.service import CacheService


@pytest.fixture
def cache_service():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return CacheService(fake)


async def test_invalidate_rankings(cache_service):
    await cache_service.set(CacheKeys.rankings_all(), "all", ttl=60)
    await cache_service.set(CacheKeys.rankings_me(42), "me", ttl=60)
    await cache_service.set(CacheKeys.teams_list(), "teams", ttl=60)

    deleted = await invalidate_rankings(cache_service)
    assert deleted == 2
    assert await cache_service.get(CacheKeys.teams_list()) == "teams"


async def test_invalidate_on_score_update(cache_service):
    await cache_service.set(CacheKeys.rankings_all(), "data", ttl=60)
    await cache_service.set(CacheKeys.match_detail(7, False, 0), "match", ttl=60)
    await cache_service.set(CacheKeys.virtual_groups(1), "vg1", ttl=60)

    await invalidate_on_score_update(cache_service)

    assert await cache_service.get(CacheKeys.rankings_all()) is None
    assert await cache_service.get(CacheKeys.match_detail(7, False, 0)) is None
    assert await cache_service.get(CacheKeys.virtual_groups(1)) is None


async def test_invalidate_on_prediction_user_scope(cache_service):
    await cache_service.set(CacheKeys.rankings_all(), "rank", ttl=60)
    await cache_service.set(CacheKeys.virtual_groups(1), "vg1", ttl=60)
    await cache_service.set(CacheKeys.virtual_groups(2), "vg2", ttl=60)

    await invalidate_on_prediction(user_id=1, cache=cache_service)

    assert await cache_service.get(CacheKeys.rankings_all()) is None
    assert await cache_service.get(CacheKeys.virtual_groups(1)) is None
    assert await cache_service.get(CacheKeys.virtual_groups(2)) == "vg2"


async def test_invalidate_subgroup_and_match(cache_service):
    await cache_service.set(
        CacheKeys.subgroup_detail(5, 1, 1, 20), "sub", ttl=60
    )
    await cache_service.set(
        CacheKeys.subgroup_detail(5, 2, 1, 20), "sub2", ttl=60
    )
    await cache_service.set(CacheKeys.subgroup_directory(1), "dir", ttl=60)
    deleted = await invalidate_subgroup(5, cache_service)
    assert deleted == 2
    assert await cache_service.get(CacheKeys.subgroup_detail(5, 1, 1, 20)) is None

    await cache_service.set(CacheKeys.match_detail(9, False, 0), "m", ttl=60)
    await cache_service.set(CacheKeys.match_detail(9, True, 3), "m2", ttl=60)
    deleted = await invalidate_match(9, cache_service)
    assert deleted == 2
    assert await cache_service.get(CacheKeys.match_detail(9, False, 0)) is None


async def test_invalidate_virtual_groups_all(cache_service):
    await cache_service.set(CacheKeys.virtual_groups(1), "a", ttl=60)
    await cache_service.set(CacheKeys.virtual_groups(2), "b", ttl=60)
    deleted = await invalidate_virtual_groups(cache_service)
    assert deleted == 2


async def test_invalidate_user_virtual_groups(cache_service):
    await cache_service.set(CacheKeys.virtual_groups(3), "a", ttl=60)
    assert await invalidate_user_virtual_groups(3, cache_service) is True
    assert await cache_service.get(CacheKeys.virtual_groups(3)) is None


async def test_invalidate_subgroup_directories(cache_service):
    await cache_service.set(CacheKeys.subgroup_directory(1), "a", ttl=60)
    await cache_service.set(CacheKeys.subgroup_directory(2), "b", ttl=60)
    from app.cache.invalidation import invalidate_subgroup_directories

    deleted = await invalidate_subgroup_directories(cache_service)
    assert deleted == 2
    assert await cache_service.get(CacheKeys.subgroup_directory(1)) is None
