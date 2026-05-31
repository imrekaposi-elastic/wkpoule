"""Unit tests for participant ranking point totals."""

from datetime import datetime, timezone

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.team import Team
from app.models.user import User
from app.models.venue import Venue
from app.services.subgroup_rankings import compute_participant_rankings


def test_compute_participant_rankings_sums_prediction_points(db):
    venue = Venue(
        name="Arena",
        city="City",
        country="USA",
        capacity=50000,
        latitude=40.0,
        longitude=-74.0,
    )
    user = User(
        username="leader",
        email="leader@example.com",
        password_hash="x",
        preferred_language="en",
    )
    home = Team(name="Home", fifa_code="HOM", group_letter="E", world_ranking=4, flag_url="")
    away = Team(name="Away", fifa_code="AWY", group_letter="E", world_ranking=14, flag_url="")
    db.add_all([venue, user, home, away])
    db.flush()
    match = Match(
        match_number=6001,
        stage="group",
        group_letter="E",
        venue_id=venue.id,
        kickoff_utc=datetime(2026, 6, 11, 18, tzinfo=timezone.utc),
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
            points=None,
        )
    )
    db.commit()

    rankings = compute_participant_rankings(db, None)

    assert len(rankings) == 1
    assert rankings[0].username == "leader"
    assert rankings[0].total_points == 12
    assert rankings[0].correct_scores == 1
    assert rankings[0].predictions_made == 1


def test_compute_participant_rankings_returns_empty_for_empty_filter(db):
    assert compute_participant_rankings(db, []) == []
