"""Unit tests for shared participant rankings cache."""

import fakeredis.aioredis
import pytest

from app.cache.keys import CacheKeys
from app.cache.service import CacheService
from app.models.user import User
from app.schemas.ranking import ParticipantRanking
from app.services.rankings_cache import (
    find_participant_ranking,
    get_cached_participant_rankings,
)
from app.services.subgroup_rankings import compute_participant_rankings


@pytest.fixture
def cache_service():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return CacheService(fake)


async def test_get_cached_participant_rankings_reuses_redis(monkeypatch, cache_service, db):
    monkeypatch.setattr("app.cache.helpers.get_cache_service", lambda: cache_service)
    calls = {"count": 0}
    original = compute_participant_rankings

    def counting_compute(session, user_ids=None):
        calls["count"] += 1
        return original(session, user_ids)

    monkeypatch.setattr(
        "app.services.rankings_cache.compute_participant_rankings",
        counting_compute,
    )

    player = User(
        username="alice",
        email="alice@example.com",
        password_hash="x",
        preferred_language="en",
    )
    db.add(player)
    db.commit()

    first = await get_cached_participant_rankings(db)
    second = await get_cached_participant_rankings(db)

    assert calls["count"] == 1
    assert len(first) == 1
    assert second == first
    assert await cache_service.get(CacheKeys.rankings_all()) is not None


def test_find_participant_ranking_returns_matching_user():
    rows = [
        ParticipantRanking(
            rank=1,
            user_id=10,
            username="alice",
            total_points=5,
            correct_results=1,
            correct_scores=0,
            correct_goal_counts=0,
            predictions_made=3,
        ),
        ParticipantRanking(
            rank=2,
            user_id=20,
            username="bob",
            total_points=2,
            correct_results=0,
            correct_scores=0,
            correct_goal_counts=0,
            predictions_made=1,
        ),
    ]

    found = find_participant_ranking(rows, 20)
    assert found is not None
    assert found.username == "bob"
    assert find_participant_ranking(rows, 99) is None
