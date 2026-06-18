"""Cache invalidation helpers for score updates, predictions, and related keys."""

from __future__ import annotations

import logging

from app.cache.keys import CacheKeys
from app.cache.service import CacheService, get_cache_service

logger = logging.getLogger("wkpoule.cache")


async def invalidate_rankings(cache: CacheService | None = None) -> int:
    service = cache or get_cache_service()
    deleted = await service.delete_pattern(CacheKeys.rankings_pattern())
    logger.debug("invalidated rankings cache (%s keys)", deleted)
    return deleted


async def invalidate_matches(cache: CacheService | None = None) -> int:
    service = cache or get_cache_service()
    deleted = await service.delete_pattern(CacheKeys.matches_pattern())
    logger.debug("invalidated matches cache (%s keys)", deleted)
    return deleted


async def invalidate_match(match_id: int, cache: CacheService | None = None) -> int:
    service = cache or get_cache_service()
    deleted = await service.delete_pattern(f"{CacheKeys.PREFIX}:matches:detail:id={match_id}:*")
    logger.debug("invalidated match %s cache (%s keys)", match_id, deleted)
    return deleted


async def invalidate_subgroup(subgroup_id: int, cache: CacheService | None = None) -> int:
    service = cache or get_cache_service()
    deleted = await service.delete_pattern(CacheKeys.subgroup_detail_pattern(subgroup_id))
    logger.debug("invalidated subgroup %s cache (%s keys)", subgroup_id, deleted)
    return deleted


async def invalidate_virtual_groups(cache: CacheService | None = None) -> int:
    service = cache or get_cache_service()
    deleted = await service.delete_pattern(CacheKeys.virtual_groups_pattern())
    logger.debug("invalidated virtual-groups cache (%s keys)", deleted)
    return deleted


async def invalidate_user_virtual_groups(user_id: int, cache: CacheService | None = None) -> bool:
    service = cache or get_cache_service()
    return await service.delete(CacheKeys.virtual_groups(user_id))


async def invalidate_teams(cache: CacheService | None = None) -> int:
    service = cache or get_cache_service()
    deleted = await service.delete_pattern(CacheKeys.teams_pattern())
    logger.debug("invalidated teams cache (%s keys)", deleted)
    return deleted


async def invalidate_on_score_update(cache: CacheService | None = None) -> None:
    """Invalidate rankings, matches, and virtual groups after a score or match status change."""
    service = cache or get_cache_service()
    await invalidate_rankings(service)
    await invalidate_matches(service)
    await invalidate_virtual_groups(service)


async def invalidate_on_prediction(
    user_id: int | None = None,
    cache: CacheService | None = None,
) -> None:
    """Invalidate rankings and virtual-group standings after a prediction change."""
    service = cache or get_cache_service()
    await invalidate_rankings(service)
    if user_id is not None:
        await invalidate_user_virtual_groups(user_id, service)
    else:
        await invalidate_virtual_groups(service)
