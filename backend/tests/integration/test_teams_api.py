"""Integration tests for teams API."""

from app.models.team import Team
from app.services.team_content import apply_team_content


def _seed_team(db, fifa_code: str = "NED", name: str = "Netherlands") -> Team:
    team = Team(
        name=name,
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
    response = client.get("/api/teams")
    assert response.status_code == 401


def test_list_teams_returns_profiled_teams(client, db, auth_headers):
    _seed_team(db)

    response = client.get("/api/teams", headers=auth_headers)

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["fifa_code"] == "NED"
    assert rows[0]["qualification_en"]
    assert rows[0]["qualification_de"]
    assert rows[0]["qualification_he"]


def test_get_team_returns_players_and_localized_profile(client, db, auth_headers):
    team = _seed_team(db)

    response = client.get("/api/teams/NED", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == team.id
    assert body["strengths_nl"]
    assert body["weaknesses_es"]
    assert len(body["players"]) >= 20
    player_names = {player["name"] for player in body["players"]}
    assert "Virgil van Dijk" in player_names
    assert body["players"][0]["position"] in {"GK", "DF", "MF", "FW"}
    assert body["qualification_data"] is not None
    assert body["qualification_data"]["standings"]
    assert any(row["highlight"] for row in body["qualification_data"]["standings"])


def test_get_team_is_case_insensitive(client, db, auth_headers):
    _seed_team(db)

    response = client.get("/api/teams/ned", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["fifa_code"] == "NED"


def test_get_team_unknown_code_returns_404(client, auth_headers):
    response = client.get("/api/teams/XYZ", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Team not found"
