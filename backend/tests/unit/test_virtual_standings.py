"""Unit tests for predicted group tables."""

from datetime import datetime, timezone

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.team import Team
from app.models.user import User
from app.models.venue import Venue
from app.services.virtual_standings import (
    best_third_place_team_ids,
    compute_virtual_group_standings,
    third_place_qualifies_for_group,
)


def _seed_predicted_group(db):
    venue = Venue(
        name="Arena",
        city="City",
        country="USA",
        capacity=50000,
        latitude=40.0,
        longitude=-74.0,
    )
    user = User(
        username="tipper",
        email="tipper@example.com",
        password_hash="x",
        preferred_language="en",
    )
    home = Team(name="Alpha", fifa_code="ALP", group_letter="B", world_ranking=5, flag_url="")
    away = Team(name="Beta", fifa_code="BET", group_letter="B", world_ranking=12, flag_url="")
    third = Team(name="Gamma", fifa_code="GAM", group_letter="B", world_ranking=30, flag_url="")
    db.add_all([venue, user, home, away, third])
    db.flush()
    match = Match(
        match_number=2001,
        stage="group",
        group_letter="B",
        venue_id=venue.id,
        kickoff_utc=datetime(2026, 6, 10, 18, tzinfo=timezone.utc),
        status="upcoming",
        home_team_id=home.id,
        away_team_id=away.id,
    )
    db.add(match)
    db.flush()
    db.add(
        Prediction(
            user_id=user.id,
            match_id=match.id,
            home_score=2,
            away_score=1,
        )
    )
    db.commit()
    return user, home, away, third


def test_compute_virtual_group_standings_uses_predictions(db):
    user, home, away, third = _seed_predicted_group(db)

    tables = compute_virtual_group_standings(db, user.id)
    group_b = next(table for table in tables if table.group_letter == "B")

    home_row = next(row for row in group_b.standings if row.team_id == home.id)
    away_row = next(row for row in group_b.standings if row.team_id == away.id)
    third_row = next(row for row in group_b.standings if row.team_id == third.id)

    assert home_row.points == 3
    assert home_row.played == 1
    assert away_row.points == 0
    assert third_row.points == 0


def test_compute_virtual_group_standings_uses_actual_result_when_match_completed(db):
    user, home, away, third = _seed_predicted_group(db)
    match = db.query(Match).filter(Match.match_number == 2001).one()
    match.status = "completed"
    match.home_score = 0
    match.away_score = 2
    db.commit()

    tables = compute_virtual_group_standings(db, user.id)
    group_b = next(table for table in tables if table.group_letter == "B")

    home_row = next(row for row in group_b.standings if row.team_id == home.id)
    away_row = next(row for row in group_b.standings if row.team_id == away.id)

    assert home_row.points == 0
    assert home_row.played == 1
    assert away_row.points == 3
    assert away_row.played == 1


def test_compute_virtual_group_standings_mixes_completed_and_predicted(db):
    user, home, away, third = _seed_predicted_group(db)
    venue = db.query(Venue).one()

    played = db.query(Match).filter(Match.match_number == 2001).one()
    played.status = "completed"
    played.home_score = 1
    played.away_score = 1

    upcoming = Match(
        match_number=2002,
        stage="group",
        group_letter="B",
        venue_id=venue.id,
        kickoff_utc=played.kickoff_utc,
        status="upcoming",
        home_team_id=home.id,
        away_team_id=third.id,
    )
    db.add(upcoming)
    db.flush()
    db.add(
        Prediction(
            user_id=user.id,
            match_id=upcoming.id,
            home_score=3,
            away_score=0,
        )
    )
    db.commit()

    tables = compute_virtual_group_standings(db, user.id)
    group_b = next(table for table in tables if table.group_letter == "B")

    home_row = next(row for row in group_b.standings if row.team_id == home.id)
    away_row = next(row for row in group_b.standings if row.team_id == away.id)
    third_row = next(row for row in group_b.standings if row.team_id == third.id)

    assert home_row.played == 2
    assert home_row.points == 4  # draw + predicted win
    assert away_row.played == 1
    assert away_row.points == 1
    assert third_row.played == 1
    assert third_row.points == 0


def test_best_third_place_team_ids_picks_top_thirds(db):
    user, home, away, third = _seed_predicted_group(db)
    tables = compute_virtual_group_standings(db, user.id)
    group_b = next(table for table in tables if table.group_letter == "B")

    best = best_third_place_team_ids(tables, top_n=1)
    third_place_id = group_b.standings[2].team_id

    assert third_place_id in best
    assert third_place_qualifies_for_group(group_b, best) is True
