"""Unit tests for subgroups router endpoints."""

from unittest.mock import patch

import pytest

from app.models.subgroup import SubgroupInvite, SubgroupMember
from app.models.user import User
from tests.seed_fixtures import make_admin


@pytest.fixture
def second_user_headers(client, db):
    register = client.post(
        "/api/auth/register",
        json={
            "username": "otheruser",
            "email": "other@example.com",
            "password": "secret12",
        },
    )
    assert register.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"username": "otheruser", "password": "secret12"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_subgroup_endpoints_require_auth(client):
    assert client.get("/api/subgroups/mine").status_code == 401
    assert client.get("/api/subgroups/directory").status_code == 401


def test_create_and_list_subgroups(client, auth_headers):
    create = client.post(
        "/api/subgroups",
        headers=auth_headers,
        json={"name": "Office Pool"},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["name"] == "Office Pool"
    assert body["my_role"] == "admin"

    mine = client.get("/api/subgroups/mine", headers=auth_headers)
    assert mine.status_code == 200
    assert len(mine.json()) == 1
    assert mine.json()[0]["name"] == "Office Pool"


def test_subgroup_directory_and_detail(client, auth_headers):
    created = client.post(
        "/api/subgroups",
        headers=auth_headers,
        json={"name": "Public Pool"},
    ).json()

    directory = client.get("/api/subgroups/directory", headers=auth_headers)
    assert directory.status_code == 200
    assert any(row["id"] == created["id"] for row in directory.json())

    detail = client.get(f"/api/subgroups/{created['id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Public Pool"


def test_subgroup_messages_flow(client, auth_headers):
    sg_id = client.post(
        "/api/subgroups",
        headers=auth_headers,
        json={"name": "Chat Pool"},
    ).json()["id"]

    empty = client.get(f"/api/subgroups/{sg_id}/messages", headers=auth_headers)
    assert empty.status_code == 200
    assert empty.json() == []

    posted = client.post(
        f"/api/subgroups/{sg_id}/messages",
        headers=auth_headers,
        json={"body": "Hello team"},
    )
    assert posted.status_code == 201
    assert posted.json()["body"] == "Hello team"

    messages = client.get(f"/api/subgroups/{sg_id}/messages", headers=auth_headers)
    assert len(messages.json()) == 1


def test_subgroup_leave(client, auth_headers):
    sg_id = client.post(
        "/api/subgroups",
        headers=auth_headers,
        json={"name": "Temporary"},
    ).json()["id"]

    leave = client.post(f"/api/subgroups/{sg_id}/leave", headers=auth_headers)
    assert leave.status_code == 204

    mine = client.get("/api/subgroups/mine", headers=auth_headers)
    assert mine.json() == []


@patch("app.routers.subgroups.send_subgroup_invite_email")
def test_subgroup_invite_and_accept(mock_email, client, db, auth_headers, second_user_headers):
    mock_email.return_value = None
    sg_id = client.post(
        "/api/subgroups",
        headers=auth_headers,
        json={"name": "Invite Pool"},
    ).json()["id"]

    other = db.query(User).filter(User.username == "otheruser").one()
    invite = client.post(
        f"/api/subgroups/{sg_id}/invites",
        headers=auth_headers,
        json={"email": other.email},
    )
    assert invite.status_code == 201

    pending = client.get("/api/subgroups/invites/pending", headers=second_user_headers)
    assert len(pending.json()) == 1
    invite_id = pending.json()[0]["id"]

    accepted = client.post(
        f"/api/subgroups/invites/{invite_id}/accept",
        headers=second_user_headers,
    )
    assert accepted.status_code == 200
    assert accepted.json()["name"] == "Invite Pool"


def test_subgroup_join_request_flow(client, auth_headers, second_user_headers):
    sg_id = client.post(
        "/api/subgroups",
        headers=auth_headers,
        json={"name": "Apply Pool"},
    ).json()["id"]

    apply = client.post(
        f"/api/subgroups/{sg_id}/join-requests",
        headers=second_user_headers,
    )
    assert apply.status_code == 201

    incoming = client.get("/api/subgroups/join-requests/incoming", headers=auth_headers)
    assert len(incoming.json()) == 1
    request_id = incoming.json()[0]["id"]

    approve = client.post(
        f"/api/subgroups/{sg_id}/join-requests/{request_id}/approve",
        headers=auth_headers,
    )
    assert approve.status_code == 200


def test_admin_can_delete_subgroup(client, db, auth_headers):
    sg_id = client.post(
        "/api/subgroups",
        headers=auth_headers,
        json={"name": "Delete Me"},
    ).json()["id"]
    make_admin(db)

    deleted = client.delete(f"/api/subgroups/{sg_id}", headers=auth_headers)
    assert deleted.status_code == 204
