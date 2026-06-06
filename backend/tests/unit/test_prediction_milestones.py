"""Unit tests for prediction milestone tracking."""

from datetime import datetime, timezone

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.subgroup import Subgroup, SubgroupMember, SubgroupMessage
from app.models.team import Team
from app.models.user import User
from app.models.venue import Venue
from app.services.prediction_milestones import (
    SUBGROUP_MESSAGE_MILESTONE_KEY,
    backfill_milestones_for_existing_users,
    list_milestones_for_user,
    record_new_milestones,
    record_subgroup_message_milestone,
)


def _seed_group_matches(db, user: User):
    venue = Venue(
        name="Arena",
        city="City",
        country="USA",
        capacity=50000,
        latitude=40.0,
        longitude=-74.0,
    )
    home = Team(name="Home", fifa_code="HOM", group_letter="A", world_ranking=1, flag_url="")
    away = Team(name="Away", fifa_code="AWY", group_letter="A", world_ranking=2, flag_url="")
    db.add_all([venue, home, away])
    db.flush()
    matches = [
        Match(
            match_number=4000 + idx,
            stage="group",
            group_letter="A",
            venue_id=venue.id,
            kickoff_utc=datetime(2026, 6, 11 + idx, 18, tzinfo=timezone.utc),
            status="upcoming",
            home_team_id=home.id,
            away_team_id=away.id,
        )
        for idx in range(2)
    ]
    db.add_all(matches)
    db.flush()
    db.add(
        Prediction(
            user_id=user.id,
            match_id=matches[0].id,
            home_score=1,
            away_score=0,
        )
    )
    db.commit()
    return matches


def test_record_new_milestones_is_idempotent(db):
    user = User(
        username="mile",
        email="mile@example.com",
        password_hash="x",
        preferred_language="en",
    )
    db.add(user)
    db.commit()
    matches = _seed_group_matches(db, user)
    db.add(
        Prediction(
            user_id=user.id,
            match_id=matches[1].id,
            home_score=0,
            away_score=0,
        )
    )
    db.commit()

    first = record_new_milestones(db, user.id)
    assert "first_prediction" in first
    assert record_new_milestones(db, user.id) == []


def test_record_new_milestones_stores_first_prediction(db):
    user = User(
        username="first",
        email="first@example.com",
        password_hash="x",
        preferred_language="en",
    )
    db.add(user)
    db.commit()
    _seed_group_matches(db, user)

    newly = record_new_milestones(db, user.id)

    assert newly == ["first_prediction"]
    stored = list_milestones_for_user(db, user.id)
    assert len(stored) == 1
    assert stored[0].milestone_key == "first_prediction"


def test_record_new_milestones_stores_completed_phase(db):
    user = User(
        username="done",
        email="done@example.com",
        password_hash="x",
        preferred_language="en",
    )
    db.add(user)
    db.commit()
    matches = _seed_group_matches(db, user)
    db.add(
        Prediction(
            user_id=user.id,
            match_id=matches[1].id,
            home_score=0,
            away_score=0,
        )
    )
    db.commit()

    newly = record_new_milestones(db, user.id)

    assert "first_prediction" in newly
    assert "group_complete" in newly
    stored = {m.milestone_key for m in list_milestones_for_user(db, user.id)}
    assert {"first_prediction", "group_complete"}.issubset(stored)
    assert "tournament_complete" in stored


def test_record_new_milestones_stores_tournament_complete(db):
    user = User(
        username="all",
        email="all@example.com",
        password_hash="x",
        preferred_language="en",
    )
    db.add(user)
    db.commit()
    matches = _seed_group_matches(db, user)
    for m in matches[1:]:
        db.add(
            Prediction(
                user_id=user.id,
                match_id=m.id,
                home_score=1,
                away_score=0,
            )
        )
    db.commit()

    newly = record_new_milestones(db, user.id)

    assert "tournament_complete" in newly


def test_record_subgroup_message_milestone(db):
    user = User(
        username="chat",
        email="chat@example.com",
        password_hash="x",
        preferred_language="en",
    )
    db.add(user)
    db.commit()
    sg = Subgroup(name="Test", created_by_user_id=user.id)
    db.add(sg)
    db.flush()
    db.add(SubgroupMember(subgroup_id=sg.id, user_id=user.id, role="admin"))
    db.add(
        SubgroupMessage(
            subgroup_id=sg.id,
            user_id=user.id,
            body="hello",
        )
    )
    db.commit()

    newly = record_subgroup_message_milestone(db, user.id)

    assert newly == [SUBGROUP_MESSAGE_MILESTONE_KEY]
    assert record_subgroup_message_milestone(db, user.id) == [SUBGROUP_MESSAGE_MILESTONE_KEY]


def test_backfill_milestones_for_existing_users(db):
    user = User(
        username="legacy",
        email="legacy@example.com",
        password_hash="x",
        preferred_language="en",
    )
    db.add(user)
    db.commit()
    _seed_group_matches(db, user)
    sg = Subgroup(name="Legacy", created_by_user_id=user.id)
    db.add(sg)
    db.flush()
    db.add(SubgroupMember(subgroup_id=sg.id, user_id=user.id, role="admin"))
    db.add(
        SubgroupMessage(
            subgroup_id=sg.id,
            user_id=user.id,
            body="old chat",
        )
    )
    db.commit()

    backfill_milestones_for_existing_users()

    stored = {m.milestone_key for m in list_milestones_for_user(db, user.id)}
    assert "first_prediction" in stored
    assert SUBGROUP_MESSAGE_MILESTONE_KEY in stored
