"""Integration tests for multilingual match search."""

from datetime import datetime, timezone

from app.models.match import Match
from app.models.team import Team
from app.models.venue import Venue


def _auth_headers(client) -> dict[str, str]:
    register = client.post(
        "/api/auth/register",
        json={
            "username": "searcher",
            "email": "searcher@example.com",
            "password": "secret12",
        },
    )
    assert register.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"username": "searcher", "password": "secret12"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_matches_search_finds_dutch_team_name(client, db):
    venue = Venue(
        name="Test Stadium",
        city="Test City",
        country="USA",
        capacity=50000,
        latitude=40.0,
        longitude=-74.0,
    )
    db.add(venue)
    db.flush()

    germany = Team(
        name="Germany",
        fifa_code="GER",
        group_letter="E",
        world_ranking=3,
        flag_url="",
    )
    netherlands = Team(
        name="Netherlands",
        fifa_code="NED",
        group_letter="E",
        world_ranking=7,
        flag_url="",
    )
    db.add_all([germany, netherlands])
    db.flush()

    db.add(
        Match(
            match_number=9001,
            stage="group",
            group_letter="E",
            home_team_id=germany.id,
            away_team_id=netherlands.id,
            venue_id=venue.id,
            kickoff_utc=datetime(2026, 6, 25, 16, tzinfo=timezone.utc),
            status="upcoming",
        )
    )
    db.commit()

    headers = _auth_headers(client)
    response = client.get("/api/matches", params={"search": "duitsland"}, headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["home_team"]["fifa_code"] == "GER"


def test_list_matches_search_finds_dutch_netherlands_name(client, db):
    venue = Venue(
        name="Arena",
        city="Amsterdam",
        country="Netherlands",
        capacity=50000,
        latitude=52.0,
        longitude=4.0,
    )
    db.add(venue)
    db.flush()

    netherlands = Team(
        name="Netherlands",
        fifa_code="NED",
        group_letter="F",
        world_ranking=7,
        flag_url="",
    )
    brazil = Team(
        name="Brazil",
        fifa_code="BRA",
        group_letter="F",
        world_ranking=1,
        flag_url="",
    )
    db.add_all([netherlands, brazil])
    db.flush()

    db.add(
        Match(
            match_number=9002,
            stage="group",
            group_letter="F",
            home_team_id=netherlands.id,
            away_team_id=brazil.id,
            venue_id=venue.id,
            kickoff_utc=datetime(2026, 6, 26, 16, tzinfo=timezone.utc),
            status="upcoming",
        )
    )
    db.commit()

    headers = _auth_headers(client)
    response = client.get("/api/matches", params={"search": "nederland"}, headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["home_team"]["fifa_code"] == "NED"
