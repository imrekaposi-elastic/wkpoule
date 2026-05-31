"""Apply editorial profiles and illustrative squads to Team rows."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.data.team_profiles import build_team_profile
from app.data.team_squads import build_team_squad
from app.models.team import Team
from app.models.team_player import TeamPlayer


def apply_team_content(db: Session, team: Team) -> None:
    profile = build_team_profile(
        team.name,
        team.fifa_code,
        team.group_letter,
        team.world_ranking,
    )
    for key, value in profile.items():
        setattr(team, key, value)

    if team.players:
        return

    for player in build_team_squad(team.fifa_code, team.name, team.world_ranking):
        db.add(TeamPlayer(team_id=team.id, **player))


def backfill_all_teams(db: Session) -> None:
    teams = db.query(Team).order_by(Team.id).all()
    for team in teams:
        apply_team_content(db, team)
    db.commit()
