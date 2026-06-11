from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.pagination import DEFAULT_PAGE_SIZE, PaginatedResponse, paginate_list
from app.schemas.ranking import GroupTable, ParticipantRanking
from app.services.group_rankings import compute_group_standings
from app.services.rankings_cache import (
    find_participant_ranking,
    get_cached_participant_rankings,
)

router = APIRouter()


@router.get("/rankings", response_model=PaginatedResponse[ParticipantRanking])
async def get_rankings(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=20),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    all_rankings = await get_cached_participant_rankings(db)
    return paginate_list(all_rankings, page, page_size)


@router.get("/rankings/me", response_model=ParticipantRanking | None)
async def get_my_ranking(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    all_rankings = await get_cached_participant_rankings(db)
    return find_participant_ranking(all_rankings, user.id)


@router.get("/groups", response_model=list[GroupTable])
def get_groups(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return compute_group_standings(db)
