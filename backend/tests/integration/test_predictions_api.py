"""Integration tests for predictions API."""

from datetime import datetime, timedelta, timezone

from app.models.match import Match
from app.models.team import Team
from app.models.venue import Venue
from app.services.prediction_lock import PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF


def _seed_match(
    db,
    *,
    kickoff_utc: datetime,
    status: str = "upcoming",
    match_number: int = 9100,
) -> Match:
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
        match_number=match_number,
        stage="group",
        group_letter="A",
        home_team_id=home.id,
        away_team_id=away.id,
        venue_id=venue.id,
        kickoff_utc=kickoff_utc,
        status=status,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def _seed_upcoming_match(db) -> Match:
    return _seed_match(
        db,
        kickoff_utc=datetime.now(timezone.utc) + timedelta(days=7),
    )


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


def test_upsert_prediction_rejected_within_lock_window(client, db, auth_headers):
    kickoff = datetime.now(timezone.utc) + timedelta(
        minutes=PREDICTION_LOCK_MINUTES_BEFORE_KICKOFF - 1
    )
    match = _seed_match(db, kickoff_utc=kickoff, match_number=9103)

    response = client.put(
        f"/api/predictions/{match.id}",
        headers=auth_headers,
        json={"home_score": 1, "away_score": 0},
    )

    assert response.status_code == 400
    assert "30 minutes" in response.json()["detail"]


def test_upsert_prediction_rejected_for_completed_match(client, db, auth_headers):
    kickoff = datetime.now(timezone.utc) + timedelta(days=3)
    match = _seed_match(
        db,
        kickoff_utc=kickoff,
        status="completed",
        match_number=9104,
    )

    response = client.put(
        f"/api/predictions/{match.id}",
        headers=auth_headers,
        json={"home_score": 2, "away_score": 2},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Predictions are locked for this match"


def test_upsert_prediction_rejected_after_kickoff(client, db, auth_headers):
    match = _seed_match(
        db,
        kickoff_utc=datetime.now(timezone.utc) - timedelta(minutes=5),
        match_number=9105,
    )

    response = client.put(
        f"/api/predictions/{match.id}",
        headers=auth_headers,
        json={"home_score": 0, "away_score": 1},
    )

    assert response.status_code == 400
    assert "30 minutes" in response.json()["detail"]
