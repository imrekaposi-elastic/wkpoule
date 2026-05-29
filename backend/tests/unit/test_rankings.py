"""Participant rankings exclude non-playing site administrators."""

from app.models.user import User
from app.services.subgroup_rankings import compute_participant_rankings


def test_global_rankings_exclude_admin_users(db):
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash="x",
        is_admin=True,
        include_in_rankings=False,
        preferred_language="en",
    )
    player = User(
        username="alice",
        email="alice@example.com",
        password_hash="x",
        is_admin=False,
        preferred_language="en",
    )
    db.add_all([admin, player])
    db.commit()

    rankings = compute_participant_rankings(db, None)
    usernames = [r.username for r in rankings]

    assert "alice" in usernames
    assert "admin" not in usernames


def test_subgroup_rankings_exclude_admin_users(db):
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash="x",
        is_admin=True,
        include_in_rankings=False,
        preferred_language="en",
    )
    player = User(
        username="bob",
        email="bob@example.com",
        password_hash="x",
        is_admin=False,
        preferred_language="en",
    )
    db.add_all([admin, player])
    db.commit()

    rankings = compute_participant_rankings(db, [admin.id, player.id])
    usernames = [r.username for r in rankings]

    assert usernames == ["bob"]


def test_admin_with_rankings_toggle_on_is_listed(db):
    admin = User(
        username="coach",
        email="coach@example.com",
        password_hash="x",
        is_admin=True,
        include_in_rankings=True,
        preferred_language="en",
    )
    player = User(
        username="carol",
        email="carol@example.com",
        password_hash="x",
        is_admin=False,
        preferred_language="en",
    )
    db.add_all([admin, player])
    db.commit()

    rankings = compute_participant_rankings(db, None)
    usernames = [r.username for r in rankings]

    assert "coach" in usernames
    assert "carol" in usernames


def test_user_hidden_when_rankings_toggle_off(db):
    hidden = User(
        username="colleague",
        email="colleague@example.com",
        password_hash="x",
        is_admin=True,
        include_in_rankings=False,
        preferred_language="en",
    )
    player = User(
        username="carol",
        email="carol@example.com",
        password_hash="x",
        is_admin=False,
        preferred_language="en",
    )
    db.add_all([hidden, player])
    db.commit()

    rankings = compute_participant_rankings(db, None)
    usernames = [r.username for r in rankings]

    assert usernames == ["carol"]
