"""Integration tests for authentication API flows."""


def test_register_login_and_me(client):
    register = client.post(
        "/api/auth/register",
        json={
            "username": "player1",
            "email": "player1@example.com",
            "password": "secret12",
            "preferred_language": "nl",
        },
    )
    assert register.status_code == 201
    assert register.json()["username"] == "player1"
    assert register.json()["preferred_language"] == "nl"

    login = client.post(
        "/api/auth/login",
        json={"username": "player1", "password": "secret12"},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "player1@example.com"


def test_register_rejects_duplicate_username(client):
    payload = {
        "username": "dupuser",
        "email": "first@example.com",
        "password": "secret12",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201

    second = client.post(
        "/api/auth/register",
        json={**payload, "email": "second@example.com"},
    )
    assert second.status_code == 400
    assert "Username" in second.json()["detail"]


def test_login_rejects_invalid_credentials(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "lockedout",
            "email": "locked@example.com",
            "password": "secret12",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={"username": "lockedout", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_refresh_issues_new_tokens(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "refresher",
            "email": "refresh@example.com",
            "password": "secret12",
        },
    )
    login = client.post(
        "/api/auth/login",
        json={"username": "refresher", "password": "secret12"},
    )
    refresh = client.post(
        "/api/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]
    assert refresh.json()["refresh_token"]
