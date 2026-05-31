"""Unit tests for persisted scoring recalculation."""

from datetime import datetime, timezone

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.team import Team
from app.models.user import User
from app.models.venue import Venue
from app.services.scoring import recalculate_points


def _seed_scored_match(db):
    venue = Venue(
        name="Arena",
        city="City",
        country="USA",
        capacity=50000,
        latitude=40.0,
        longitude=-74.0,
    )
    user = User(
        username="scorer",
        email="scorer@example.com",
        password_hash="x",
        preferred_language="en",
    )
    home = Team(name="Home", fifa_code="HOM", group_letter="C", world_ranking=10, flag_url="")
    away = Team(name="Away", fifa_code="AWY", group_letter="C", world_ranking=20, flag_url="")
    db.add_all([venue, user, home, away])
    db.flush()
    match = Match(
        match_number=3001,
        stage="group",
        group_letter="C",
        venue_id=venue.id,
        kickoff_utc=datetime(2026, 6, 12, 18, tzinfo=timezone.utc),
        status="completed",
        home_team_id=home.id,
        away_team_id=away.id,
        home_score=2,
        away_score=1,
    )
    db.add(match)
    db.flush()
    db.add(
        Prediction(
            user_id=user.id,
            match_id=match.id,
            home_score=2,
            away_score=1,
            points=0,
        )
    )
    db.commit()
    return user, match


def test_recalculate_points_updates_stored_prediction_points(db):
    user, match = _seed_scored_match(db)

    updated = recalculate_points()

    assert updated == 1
    prediction = (
        db.query(Prediction)
        .filter(Prediction.user_id == user.id, Prediction.match_id == match.id)
        .one()
    )
    assert prediction.points == 12


def test_recalculate_points_returns_zero_without_completed_matches(db):
    assert recalculate_points() == 0
