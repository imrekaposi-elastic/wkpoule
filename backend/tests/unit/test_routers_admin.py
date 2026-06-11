"""Unit tests for admin router endpoints."""

from tests.seed_fixtures import make_admin


def test_admin_routes_require_admin(client, auth_headers):
    assert client.get("/api/admin/users", headers=auth_headers).status_code == 403


def test_admin_list_and_patch_user(client, db, auth_headers):
    make_admin(db)

    users = client.get("/api/admin/users", headers=auth_headers)
    assert users.status_code == 200
    assert len(users.json()) >= 1

    user_id = users.json()[0]["id"]
    patched = client.patch(
        f"/api/admin/users/{user_id}",
        headers=auth_headers,
        json={"include_in_rankings": False},
    )
    assert patched.status_code == 200
    assert patched.json()["include_in_rankings"] is False


def test_admin_reset_password(client, db, auth_headers):
    make_admin(db)
    users = client.get("/api/admin/users", headers=auth_headers).json()
    user_id = next(u["id"] for u in users if u["username"] == "testuser")

    reset = client.post(
        f"/api/admin/users/{user_id}/password",
        headers=auth_headers,
        json={"new_password": "newsecret1"},
    )
    assert reset.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "newsecret1"},
    )
    assert login.status_code == 200


def test_admin_subgroups(client, db, auth_headers):
    make_admin(db)
    client.post(
        "/api/subgroups",
        headers=auth_headers,
        json={"name": "Admin View"},
    )

    subgroups = client.get("/api/admin/subgroups", headers=auth_headers)
    assert subgroups.status_code == 200
    assert len(subgroups.json()) >= 1
