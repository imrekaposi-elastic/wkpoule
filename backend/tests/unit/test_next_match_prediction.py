"""Unit tests for next-match prediction helper."""

from datetime import datetime, timedelta, timezone

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.team import Team
from app.models.user import User
from app.models.venue import Venue
from app.services.next_match_prediction import first_match_needing_prediction


def test_first_match_needing_prediction_skips_predicted_matches(db):
    venue = Venue(
        name="Arena",
        city="City",
        country="USA",
        capacity=50000,
        latitude=40.0,
        longitude=-74.0,
    )
    user = User(
        username="picker",
        email="picker@example.com",
        password_hash="x",
        preferred_language="en",
    )
    home = Team(name="Home", fifa_code="HOM", group_letter="D", world_ranking=8, flag_url="")
    away = Team(name="Away", fifa_code="AWY", group_letter="D", world_ranking=18, flag_url="")
    db.add_all([venue, user, home, away])
    db.flush()
    first = Match(
        match_number=5001,
        stage="group",
        group_letter="D",
        venue_id=venue.id,
        kickoff_utc=datetime.now(timezone.utc) - timedelta(hours=1),
        status="upcoming",
        home_team_id=home.id,
        away_team_id=away.id,
    )
    second = Match(
        match_number=5002,
        stage="group",
        group_letter="D",
        venue_id=venue.id,
        kickoff_utc=datetime.now(timezone.utc) + timedelta(days=2),
        status="upcoming",
        home_team_id=away.id,
        away_team_id=home.id,
    )
    db.add_all([first, second])
    db.flush()
    db.add(Prediction(user_id=user.id, match_id=first.id, home_score=1, away_score=1))
    db.commit()

    next_match = first_match_needing_prediction(db, user.id)

    assert next_match is not None
    assert next_match.id == second.id


def test_first_match_needing_prediction_within_stage_after_current(db):
    venue = Venue(
        name="Arena",
        city="City",
        country="USA",
        capacity=50000,
        latitude=40.0,
        longitude=-74.0,
    )
    user = User(
        username="knockout",
        email="knockout@example.com",
        password_hash="x",
        preferred_language="en",
    )
    home = Team(name="Home", fifa_code="HOM", group_letter="D", world_ranking=8, flag_url="")
    away = Team(name="Away", fifa_code="AWY", group_letter="D", world_ranking=18, flag_url="")
    db.add_all([venue, user, home, away])
    db.flush()
    group_match = Match(
        match_number=72,
        stage="group",
        group_letter="D",
        venue_id=venue.id,
        kickoff_utc=datetime.now(timezone.utc) + timedelta(days=1),
        status="upcoming",
        home_team_id=home.id,
        away_team_id=away.id,
    )
    first_ko = Match(
        match_number=73,
        stage="round_of_32",
        group_letter=None,
        venue_id=venue.id,
        kickoff_utc=datetime.now(timezone.utc) + timedelta(days=2),
        status="upcoming",
        home_team_id=home.id,
        away_team_id=away.id,
    )
    second_ko = Match(
        match_number=74,
        stage="round_of_32",
        group_letter=None,
        venue_id=venue.id,
        kickoff_utc=datetime.now(timezone.utc) + timedelta(days=3),
        status="upcoming",
        home_team_id=away.id,
        away_team_id=home.id,
    )
    db.add_all([group_match, first_ko, second_ko])
    db.flush()
    db.add(Prediction(user_id=user.id, match_id=first_ko.id, home_score=2, away_score=1))
    db.commit()

    next_match = first_match_needing_prediction(
        db,
        user.id,
        stage="round_of_32",
        after_match_number=73,
    )

    assert next_match is not None
    assert next_match.id == second_ko.id
