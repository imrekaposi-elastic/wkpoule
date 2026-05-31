from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.team import Team
from app.routers.auth import get_current_user
from app.schemas.team import TeamDetailOut, TeamSummaryOut

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamSummaryOut])
def list_teams(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return (
        db.query(Team)
        .order_by(Team.group_letter, Team.world_ranking, Team.name)
        .all()
    )


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
    return team
