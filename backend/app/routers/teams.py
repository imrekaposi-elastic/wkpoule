from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.data.team_qualification_data import build_qualification_data
from app.cache.helpers import cached_call, run_cache_task
from app.cache.invalidation import invalidate_subgroup
from app.cache.keys import CacheKeys
from app.cache.ttl import TEAMS_TTL
from app.database import get_db
from app.models.team import Team
from app.routers.auth import get_current_user
from app.schemas.team import QualificationDataOut, TeamDetailOut, TeamSummaryOut

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamSummaryOut])
async def list_teams(db: Session = Depends(get_db), _=Depends(get_current_user)):
    cache_key = CacheKeys.teams_list()

    def compute() -> list[TeamSummaryOut]:
        teams = (
            db.query(Team)
            .order_by(Team.group_letter, Team.world_ranking, Team.name)
            .all()
        )
        return [TeamSummaryOut.model_validate(team) for team in teams]

    return await cached_call(cache_key, TEAMS_TTL, list[TeamSummaryOut], compute)


@router.get("/{fifa_code}", response_model=TeamDetailOut)
def get_team(fifa_code: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    team = (
        db.query(Team)
        .options(joinedload(Team.players))
        .filter(Team.fifa_code == fifa_code.upper())
        .first()
    )
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    detail = TeamDetailOut.model_validate(team)
    if detail.qualification_data is None:
        raw = build_qualification_data(team.fifa_code)
        if raw:
            detail.qualification_data = QualificationDataOut.model_validate(raw)
    return detail
