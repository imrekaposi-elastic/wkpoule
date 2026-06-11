"""Unit tests for rankings and predictions router endpoints."""

from tests.seed_fixtures import seed_group_match


def test_rankings_endpoints(client, auth_headers):
    rankings = client.get("/api/rankings", headers=auth_headers)
    assert rankings.status_code == 200
    assert "items" in rankings.json()

    me = client.get("/api/rankings/me", headers=auth_headers)
    assert me.status_code == 200

    groups = client.get("/api/groups", headers=auth_headers)
    assert groups.status_code == 200
    assert isinstance(groups.json(), list)


def test_prediction_milestones_requires_auth(client):
    assert client.get("/api/predictions/milestones").status_code == 401


def test_prediction_milestones_empty(client, auth_headers):
    response = client.get("/api/predictions/milestones", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_upsert_prediction(client, db, auth_headers):
    match = seed_group_match(db, match_number=9100)

    response = client.put(
        f"/api/predictions/{match.id}",
        headers=auth_headers,
        json={"home_score": 2, "away_score": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["home_score"] == 2
    assert "first_prediction" in body["newly_achieved"]


def test_virtual_groups_and_mine_brief(client, db, auth_headers):
    match = seed_group_match(db, match_number=9101)
    client.put(
        f"/api/predictions/{match.id}",
        headers=auth_headers,
        json={"home_score": 1, "away_score": 0},
    )

    virtual = client.get("/api/predictions/virtual-groups", headers=auth_headers)
    assert virtual.status_code == 200
    assert len(virtual.json()) >= 1

    brief = client.get("/api/predictions/mine/brief", headers=auth_headers)
    assert brief.status_code == 200
    assert len(brief.json()) >= 1


def test_match_predictions_by_outcome(client, db, auth_headers):
    match = seed_group_match(db, match_number=9102)
    client.put(
        f"/api/predictions/{match.id}",
        headers=auth_headers,
        json={"home_score": 3, "away_score": 0},
    )

    home_wins = client.get(
        f"/api/predictions/match/{match.id}/by-outcome",
        params={"outcome": "home_win"},
        headers=auth_headers,
    )
    assert home_wins.status_code == 200
    assert len(home_wins.json()) >= 1
