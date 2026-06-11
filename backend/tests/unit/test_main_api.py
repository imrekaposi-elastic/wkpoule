"""Unit tests for FastAPI app endpoints."""

from unittest.mock import AsyncMock, patch


def test_health_check(client):
    with patch("app.main.redis_ping", new=AsyncMock(return_value=True)):
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["redis"] == "ok"


def test_health_check_redis_unavailable(client):
    with patch("app.main.redis_ping", new=AsyncMock(return_value=False)):
        response = client.get("/api/health")
    assert response.json()["redis"] == "unavailable"
