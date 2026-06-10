"""Cache service abstraction with JSON helpers and fail-open semantics."""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter

from app.cache.redis_client import get_redis

logger = logging.getLogger("wkpoule.cache")

T = TypeVar("T")

_cache_service: CacheService | None = None


class CacheService:
    """Thin async wrapper around Redis with graceful degradation on errors."""

    def __init__(self, redis_client=None) -> None:
        self._redis = redis_client

    async def get(self, key: str) -> str | None:
        if self._redis is None:
            return None
        try:
            return await self._redis.get(key)
        except Exception as exc:
            logger.warning("cache get failed for %s: %s", key, exc)
            return None

    async def set(self, key: str, value: str, ttl: int) -> bool:
        if self._redis is None:
            return False
        try:
            await self._redis.set(key, value, ex=ttl)
            return True
        except Exception as exc:
            logger.warning("cache set failed for %s: %s", key, exc)
            return False

    async def delete(self, key: str) -> bool:
        if self._redis is None:
            return False
        try:
            deleted = await self._redis.delete(key)
            return deleted > 0
        except Exception as exc:
            logger.warning("cache delete failed for %s: %s", key, exc)
            return False

    async def delete_pattern(self, pattern: str) -> int:
        if self._redis is None:
            return 0
        deleted = 0
        try:
            async for key in self._redis.scan_iter(match=pattern, count=100):
                deleted += int(await self._redis.delete(key))
        except Exception as exc:
            logger.warning("cache delete_pattern failed for %s: %s", pattern, exc)
        return deleted

    async def get_json(self, key: str, model: type[T]) -> T | None:
        raw = await self.get(key)
        if raw is None:
            return None
        try:
            return TypeAdapter(model).validate_json(raw)
        except Exception as exc:
            logger.warning("cache get_json failed for %s: %s", key, exc)
            return None

    async def set_json(self, key: str, value: Any, ttl: int) -> bool:
        try:
            if isinstance(value, BaseModel):
                payload = value.model_dump_json()
            else:
                payload = json.dumps(value, default=str)
            return await self.set(key, payload, ttl)
        except Exception as exc:
            logger.warning("cache set_json failed for %s: %s", key, exc)
            return False


def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(get_redis())
    return _cache_service


def reset_cache_service() -> None:
    global _cache_service
    _cache_service = None
