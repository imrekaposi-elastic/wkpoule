"""Unit tests for teams and venues routers."""

from app.models.team import Team
from app.models.venue import Venue
from app.services.team_content import apply_team_content


def _seed_team(db, fifa_code: str = "NED") -> Team:
    team = Team(
        name="Netherlands",
        fifa_code=fifa_code,
        group_letter="F",
        world_ranking=7,
        flag_url="https://example.com/ned.svg",
    )
    db.add(team)
    db.flush()
    apply_team_content(db, team)
    db.commit()
    db.refresh(team)
    return team


def test_list_teams_requires_auth(client):
    assert client.get("/api/teams").status_code == 401


def test_get_team_returns_detail(client, db, auth_headers):
    team = _seed_team(db)

    response = client.get("/api/teams/NED", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == team.id
    assert body["qualification_data"]["standings"]


def test_get_team_unknown_code_returns_404(client, auth_headers):
    response = client.get("/api/teams/XYZ", headers=auth_headers)

    assert response.status_code == 404


def test_list_venues_includes_scheduled_matches(client, db, auth_headers):
    venue = Venue(
        name="Final Arena",
        city="Final City",
        country="USA",
        capacity=80000,
        latitude=40.0,
        longitude=-74.0,
        review_en="Review",
    )
    db.add(venue)
    db.commit()

    response = client.get("/api/venues", headers=auth_headers)

    assert response.status_code == 200
    rows = response.json()
    assert rows[0]["name"] == "Final Arena"
    assert rows[0]["matches"] == []
