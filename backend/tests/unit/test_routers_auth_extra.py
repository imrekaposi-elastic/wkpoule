"""Unit tests for auth router endpoints."""


def test_auth_me(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_refresh_token(client, auth_headers):
    login = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "secret12"},
    )
    refresh_token = login.json()["refresh_token"]

    refreshed = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]


def test_update_language(client, auth_headers):
    response = client.patch(
        "/api/auth/me/language",
        headers=auth_headers,
        json={"language": "nl"},
    )
    assert response.status_code == 200
    assert response.json()["preferred_language"] == "nl"


def test_self_service_reset_password(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "resetme",
            "email": "reset@example.com",
            "password": "secret12",
        },
    )

    reset = client.post(
        "/api/auth/reset-password",
        json={
            "username": "resetme",
            "email": "reset@example.com",
            "new_password": "newsecret1",
        },
    )
    assert reset.status_code == 204

    login = client.post(
        "/api/auth/login",
        json={"username": "resetme", "password": "newsecret1"},
    )
    assert login.status_code == 200


def test_register_duplicate_username(client):
    payload = {
        "username": "dupe",
        "email": "dupe@example.com",
        "password": "secret12",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    dup = client.post(
        "/api/auth/register",
        json={**payload, "email": "other@example.com"},
    )
    assert dup.status_code == 400


def test_update_profile(client, auth_headers):
    response = client.patch(
        "/api/auth/me",
        headers=auth_headers,
        json={"email": "updated@example.com"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "updated@example.com"
