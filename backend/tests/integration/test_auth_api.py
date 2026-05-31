"""Integration tests for authentication API flows."""

import logging

from app.models.subgroup import Subgroup, SubgroupMember


def test_register_login_and_me(client):
    register = client.post(
        "/api/auth/register",
        json={
            "username": "player1",
            "email": "player1@example.com",
            "password": "secret12",
            "preferred_language": "es",
        },
    )
    assert register.status_code == 201
    assert register.json()["username"] == "player1"
    assert register.json()["preferred_language"] == "es"

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


def test_register_elastic_email_joins_elastic_subgroup(client, db):
    register = client.post(
        "/api/auth/register",
        json={
            "username": "elasticdev",
            "email": "Dev@Elastic.CO",
            "password": "secret12",
        },
    )
    assert register.status_code == 201
    assert register.json()["email"] == "dev@elastic.co"
    assert register.json()["is_admin"] is False

    user_id = register.json()["id"]
    sg = db.query(Subgroup).filter(Subgroup.name == "Elastic").one()
    member = (
        db.query(SubgroupMember)
        .filter(
            SubgroupMember.subgroup_id == sg.id,
            SubgroupMember.user_id == user_id,
        )
        .one()
    )
    assert member.role == "member"

    login = client.post(
        "/api/auth/login",
        json={"username": "elasticdev", "password": "secret12"},
    )
    mine = client.get(
        "/api/subgroups/mine",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert mine.status_code == 200
    assert any(s["name"] == "Elastic" for s in mine.json())


def test_register_rejects_duplicate_username(client):
    payload = {
        "username": "dupuser",
        "email": "first@example.com",
        "password": "secret12",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201

    second = client.post(
        "/api/auth/register",
        json={**payload, "email": "second@example.com", "username": "DupUser"},
    )
    assert second.status_code == 400
    assert "Username" in second.json()["detail"]


def test_login_is_case_insensitive(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "Imre.Kaposi",
            "email": "imre@example.com",
            "password": "secret12",
        },
    )

    login = client.post(
        "/api/auth/login",
        json={"username": "iMre.KAPOsi", "password": "secret12"},
    )
    assert login.status_code == 200


def test_register_stores_lowercase_username(client):
    register = client.post(
        "/api/auth/register",
        json={
            "username": "Mixed.Case",
            "email": "mixed@example.com",
            "password": "secret12",
        },
    )
    assert register.status_code == 201
    assert register.json()["username"] == "mixed.case"


def test_login_rejects_invalid_credentials(client, caplog):
    client.post(
        "/api/auth/register",
        json={
            "username": "lockedout",
            "email": "locked@example.com",
            "password": "secret12",
        },
    )

    with caplog.at_level(logging.INFO, logger="app.routers.auth"):
        response = client.post(
            "/api/auth/login",
            json={"username": "lockedout", "password": "wrong-password"},
        )
    assert response.status_code == 401
    failure_logs = [
        r for r in caplog.records if r.__dict__.get("event.action") == "user_login_failure"
    ]
    assert len(failure_logs) == 1
    record = failure_logs[0]
    assert record.getMessage() == "Failed login for lockedout"
    assert record.__dict__["event.outcome"] == "failure"
    assert record.__dict__["user.name"] == "lockedout"


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
