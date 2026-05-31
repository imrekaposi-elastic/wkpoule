"""Unit tests for username normalization helpers."""

from app.models.user import User
from app.username import get_user_by_username, normalize_username


def test_normalize_username_lowercases_and_trims():
    assert normalize_username("  Alice  ") == "alice"


def test_get_user_by_username_is_case_insensitive(db):
    user = User(
        username="alice",
        email="alice@example.com",
        password_hash="x",
        preferred_language="en",
    )
    db.add(user)
    db.commit()

    found = get_user_by_username(db, "ALICE")

    assert found is not None
    assert found.username == "alice"
