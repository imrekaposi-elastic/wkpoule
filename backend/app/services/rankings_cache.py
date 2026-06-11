"""Shared Redis-backed cache for global participant rankings."""

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.cache.helpers import cached_call
from app.cache.keys import CacheKeys
from app.cache.ttl import RANKINGS_TTL
from app.schemas.ranking import ParticipantRanking
from app.services.subgroup_rankings import compute_participant_rankings


class _ParticipantRankingsCache(BaseModel):
    rankings: list[ParticipantRanking]


async def get_cached_participant_rankings(db: Session) -> list[ParticipantRanking]:
    """Return the full rankings table, computing at most once per TTL window."""

    def compute() -> _ParticipantRankingsCache:
        return _ParticipantRankingsCache(
            rankings=compute_participant_rankings(db, None),
        )

    cached = await cached_call(
        CacheKeys.rankings_all(),
        RANKINGS_TTL,
        _ParticipantRankingsCache,
        compute,
    )
    return cached.rankings


def find_participant_ranking(
    rankings: list[ParticipantRanking],
    user_id: int,
) -> ParticipantRanking | None:
    for row in rankings:
        if row.user_id == user_id:
            return row
    return None
