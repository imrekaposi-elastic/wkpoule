"""Match prediction list must not include admin tips."""

from datetime import datetime, timezone

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.team import Team
from app.models.user import User
from app.models.venue import Venue


def _seed_match(db) -> Match:
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
        match_number=9200,
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


def test_match_predictions_exclude_admin(client, db, auth_headers):
    match = _seed_match(db)
    admin = db.query(User).filter(User.is_admin.is_(True)).first()
    assert admin is not None

    viewer_id = db.query(User).filter(User.id != admin.id).first().id
    db.add_all(
        [
            Prediction(
                user_id=admin.id,
                match_id=match.id,
                home_score=3,
                away_score=0,
            ),
            Prediction(
                user_id=viewer_id,
                match_id=match.id,
                home_score=1,
                away_score=1,
            ),
        ]
    )
    db.commit()

    response = client.get(
        f"/api/predictions/match/{match.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["username"] != "admin"
    assert items[0]["home_score"] == 1
    assert items[0]["away_score"] == 1
