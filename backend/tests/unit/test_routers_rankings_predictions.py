"""Unit tests for rankings and predictions router endpoints."""

from unittest.mock import patch

import fakeredis.aioredis
import pytest

from app.cache.service import CacheService
from app.services import rankings_cache
from tests.seed_fixtures import seed_group_match


@pytest.fixture
def rankings_cache_service(monkeypatch):
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    service = CacheService(fake)
    monkeypatch.setattr("app.cache.helpers.get_cache_service", lambda: service)
    return service


def test_rankings_me_reuses_shared_rankings_cache(client, auth_headers, rankings_cache_service):
    calls = {"count": 0}
    original = rankings_cache.compute_participant_rankings

    def counting_compute(session, user_ids=None):
        calls["count"] += 1
        return original(session, user_ids)

    with patch.object(rankings_cache, "compute_participant_rankings", counting_compute):
        rankings = client.get("/api/rankings", headers=auth_headers)
        me = client.get("/api/rankings/me", headers=auth_headers)

    assert rankings.status_code == 200
    assert me.status_code == 200
    assert calls["count"] == 1
    assert me.json() is not None
    assert me.json()["user_id"] == rankings.json()["items"][0]["user_id"]


def test_rankings_endpoints(client, auth_headers):
    rankings = client.get("/api/rankings", headers=auth_headers)
    assert rankings.status_code == 200
    assert "items" in rankings.json()

    me = client.get("/api/rankings/me", headers=auth_headers)
    assert me.status_code == 200

    groups = client.get("/api/groups", headers=auth_headers)
    assert groups.status_code == 200
    assert isinstance(groups.json(), list)


def test_prediction_milestones_requires_auth(client):
    assert client.get("/api/predictions/milestones").status_code == 401


def test_prediction_milestones_empty(client, auth_headers):
    response = client.get("/api/predictions/milestones", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_upsert_prediction(client, db, auth_headers):
    match = seed_group_match(db, match_number=9100)

    response = client.put(
        f"/api/predictions/{match.id}",
        headers=auth_headers,
        json={"home_score": 2, "away_score": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["home_score"] == 2
    assert "first_prediction" in body["newly_achieved"]


def test_virtual_groups_and_mine_brief(client, db, auth_headers):
    match = seed_group_match(db, match_number=9101)
    client.put(
        f"/api/predictions/{match.id}",
        headers=auth_headers,
        json={"home_score": 1, "away_score": 0},
    )

    virtual = client.get("/api/predictions/virtual-groups", headers=auth_headers)
    assert virtual.status_code == 200
    assert len(virtual.json()) >= 1

    brief = client.get("/api/predictions/mine/brief", headers=auth_headers)
    assert brief.status_code == 200
    assert len(brief.json()) >= 1


def test_match_predictions_by_outcome(client, db, auth_headers):
    match = seed_group_match(db, match_number=9102)
    client.put(
        f"/api/predictions/{match.id}",
        headers=auth_headers,
        json={"home_score": 3, "away_score": 0},
    )

    home_wins = client.get(
        f"/api/predictions/match/{match.id}/by-outcome",
        params={"outcome": "home_win"},
        headers=auth_headers,
    )
    assert home_wins.status_code == 200
    assert len(home_wins.json()) >= 1
