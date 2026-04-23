from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.ranking import GroupTable, ParticipantRanking
from app.services.group_rankings import compute_group_standings
from app.services.subgroup_rankings import compute_participant_rankings

router = APIRouter()


@router.get("/rankings", response_model=list[ParticipantRanking])
def get_rankings(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return compute_participant_rankings(db, None)


@router.get("/groups", response_model=list[GroupTable])
def get_groups(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return compute_group_standings(db)
