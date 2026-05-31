"""Unit tests for auth dependency helpers."""

import pytest
from fastapi import HTTPException

from app.auth import create_access_token, get_admin_user, get_current_user
from app.models.user import User


def test_get_current_user_returns_matching_user(db):
    user = User(
        username="alice",
        email="alice@example.com",
        password_hash="x",
        preferred_language="en",
    )
    db.add(user)
    db.commit()

    token = create_access_token("alice")
    current = get_current_user(token=token, db=db)

    assert current.id == user.id


def test_get_current_user_rejects_unknown_user(db):
    token = create_access_token("missing")

    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, db=db)

    assert exc.value.status_code == 401


def test_get_admin_user_requires_admin_flag(db):
    user = User(
        username="player",
        email="player@example.com",
        password_hash="x",
        is_admin=False,
        preferred_language="en",
    )

    with pytest.raises(HTTPException) as exc:
        get_admin_user(current_user=user)

    assert exc.value.status_code == 403
