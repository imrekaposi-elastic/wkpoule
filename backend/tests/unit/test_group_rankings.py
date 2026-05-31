"""Unit tests for actual group standings from completed matches."""

from datetime import datetime, timezone

from app.models.match import Match
from app.models.team import Team
from app.models.venue import Venue
from app.services.group_rankings import (
    _apply_h2h_tiebreaker,
    _same_rank_key,
    compute_group_standings,
)


def _venue(db) -> Venue:
    venue = Venue(
        name="Test Arena",
        city="Test City",
        country="USA",
        capacity=40000,
        latitude=40.0,
        longitude=-74.0,
    )
    db.add(venue)
    db.flush()
    return venue


def _seed_group_a(db):
    venue = _venue(db)
    winner = Team(name="Winner", fifa_code="WIN", group_letter="A", world_ranking=1, flag_url="")
    loser = Team(name="Loser", fifa_code="LOS", group_letter="A", world_ranking=2, flag_url="")
    draw1 = Team(name="Draw1", fifa_code="DR1", group_letter="A", world_ranking=3, flag_url="")
    draw2 = Team(name="Draw2", fifa_code="DR2", group_letter="A", world_ranking=4, flag_url="")
    db.add_all([winner, loser, draw1, draw2])
    db.flush()
    db.add_all(
        [
            Match(
                match_number=1001,
                stage="group",
                group_letter="A",
                venue_id=venue.id,
                kickoff_utc=datetime(2026, 6, 1, 18, tzinfo=timezone.utc),
                status="completed",
                home_team_id=winner.id,
                away_team_id=loser.id,
                home_score=2,
                away_score=0,
            ),
            Match(
                match_number=1002,
                stage="group",
                group_letter="A",
                venue_id=venue.id,
                kickoff_utc=datetime(2026, 6, 2, 18, tzinfo=timezone.utc),
                status="completed",
                home_team_id=draw1.id,
                away_team_id=draw2.id,
                home_score=1,
                away_score=1,
            ),
        ]
    )
    db.commit()
    return winner, loser, draw1, draw2


def test_compute_group_standings_orders_by_points(db):
    winner, loser, draw1, draw2 = _seed_group_a(db)

    tables = compute_group_standings(db)
    group_a = next(table for table in tables if table.group_letter == "A")

    assert group_a.standings[0].team_id == winner.id
    assert group_a.standings[0].points == 3
    assert group_a.standings[0].goal_difference == 2
    assert {row.team_id for row in group_a.standings[1:]} == {draw1.id, draw2.id, loser.id}


def test_same_rank_key_detects_tied_teams():
    a = {"points": 3, "goals_for": 4, "goals_against": 2, "h2h": {}}
    b = {"points": 3, "goals_for": 4, "goals_against": 2, "h2h": {}}
    c = {"points": 1, "goals_for": 2, "goals_against": 2, "h2h": {}}

    assert _same_rank_key(a, b) is True
    assert _same_rank_key(a, c) is False


def test_h2h_tiebreaker_prefers_head_to_head_points():
    standings = [
        {"points": 3, "goals_for": 3, "goals_against": 3, "h2h": {2: 1}},
        {"points": 3, "goals_for": 3, "goals_against": 3, "h2h": {1: 3}},
    ]

    _apply_h2h_tiebreaker(standings)

    assert standings[0]["h2h"][1] == 3
