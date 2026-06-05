"""Integration tests for predictions API."""

from datetime import datetime, timezone

from app.models.match import Match
from app.models.team import Team
from app.models.venue import Venue


def _seed_upcoming_match(db) -> Match:
    venue = Venue(
        name="Arena",
        city="City",
        country="USA",
        capacity=50000,
        latitude=40.0,
        longitude=-74.0,
    )
    home = Team(
        name="Mexico",
        fifa_code="MEX",
        group_letter="A",
        world_ranking=14,
        flag_url="",
    )
    away = Team(
        name="Canada",
        fifa_code="CAN",
        group_letter="A",
        world_ranking=48,
        flag_url="",
    )
    db.add(venue)
    db.add_all([home, away])
    db.flush()
    match = Match(
        match_number=9100,
        stage="group",
        group_letter="A",
        home_team_id=home.id,
        away_team_id=away.id,
        venue_id=venue.id,
        kickoff_utc=datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc),
        status="upcoming",
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def test_prediction_milestones_requires_auth(client):
    response = client.get("/api/predictions/milestones")
    assert response.status_code == 401


def test_prediction_milestones_empty_for_new_user(client, auth_headers):
    response = client.get("/api/predictions/milestones", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_upsert_prediction_for_upcoming_match(client, db, auth_headers):
    match = _seed_upcoming_match(db)

    response = client.put(
        f"/api/predictions/{match.id}",
        headers=auth_headers,
        json={"home_score": 2, "away_score": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["match_id"] == match.id
    assert body["home_score"] == 2
    assert body["away_score"] == 1
    assert body["points"] is None
    assert "first_prediction" in body["newly_achieved"]
