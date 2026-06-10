"""Shared pytest fixtures: in-memory SQLite DB and FastAPI test client."""

from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configure test environment before importing application modules.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("WKPOULE_BOOTSTRAP_ADMIN_PASSWORD", "")

from app.config import get_settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402

get_settings.cache_clear()

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

import app.database as database  # noqa: E402

database.engine = _test_engine
database.SessionLocal = TestingSessionLocal

import app.models  # noqa: F401, E402 — register ORM mappers


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    with (
        patch("app.main.start_polling"),
        patch("app.main.stop_polling"),
        patch("app.main.init_redis", new=AsyncMock()),
        patch("app.main.close_redis", new=AsyncMock()),
    ):
        from app.main import app

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client) -> dict[str, str]:
    """Register a user and return Authorization headers for protected routes."""
    register = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "secret12",
        },
    )
    assert register.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "secret12"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
