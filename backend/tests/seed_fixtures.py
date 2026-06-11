"""Shared DB seed helpers for router tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.team import Team
from app.models.user import User
from app.models.venue import Venue


def seed_venue(db: Session, *, name: str = "Arena", city: str = "City") -> Venue:
    venue = Venue(
        name=name,
        city=city,
        country="USA",
        capacity=50000,
        latitude=40.0,
        longitude=-74.0,
    )
    db.add(venue)
    db.flush()
    return venue


def seed_team(
    db: Session,
    *,
    fifa_code: str,
    name: str | None = None,
    group_letter: str = "A",
    world_ranking: int = 10,
) -> Team:
    team = Team(
        name=name or fifa_code,
        fifa_code=fifa_code,
        group_letter=group_letter,
        world_ranking=world_ranking,
        flag_url="",
    )
    db.add(team)
    db.flush()
    return team


def seed_group_match(
    db: Session,
    *,
    match_number: int = 100,
    group_letter: str = "A",
    home_code: str = "MEX",
    away_code: str = "CAN",
    kickoff: datetime | None = None,
    status: str = "upcoming",
) -> Match:
    venue = seed_venue(db)
    home = seed_team(db, fifa_code=home_code, group_letter=group_letter, name=home_code)
    away = seed_team(db, fifa_code=away_code, group_letter=group_letter, name=away_code)
    match = Match(
        match_number=match_number,
        stage="group",
        group_letter=group_letter,
        home_team_id=home.id,
        away_team_id=away.id,
        venue_id=venue.id,
        kickoff_utc=kickoff
        or (datetime.now(timezone.utc) + timedelta(hours=2)),
        status=status,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def make_admin(db: Session, username: str = "testuser") -> User:
    user = db.query(User).filter(User.username == username).one()
    user.is_admin = True
    db.commit()
    db.refresh(user)
    return user
