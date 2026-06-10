"""OpenTelemetry metrics and spans for the wkpoule cache layer."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from opentelemetry import metrics, trace
from opentelemetry.metrics import Observation

_meter = metrics.get_meter("wkpoule.cache")
_tracer = trace.get_tracer("wkpoule.cache")
_pool_gauge_registered = False

cache_hits = _meter.create_counter(
    "wkpoule.cache.hit",
    description="Application cache hits (read-through helpers)",
)
cache_misses = _meter.create_counter(
    "wkpoule.cache.miss",
    description="Application cache misses (read-through helpers)",
)
operation_duration = _meter.create_histogram(
    "wkpoule.cache.operation.duration",
    unit="ms",
    description="Cache operation latency",
)
operation_errors = _meter.create_counter(
    "wkpoule.cache.operation.error",
    description="Cache operation failures",
)


def cache_endpoint_from_key(key: str) -> str:
    parts = key.split(":")
    if len(parts) >= 2 and parts[0] == "wkpoule":
        return parts[1]
    return "unknown"


def record_cache_hit(key: str) -> None:
    cache_hits.add(1, {"cache.endpoint": cache_endpoint_from_key(key)})


def record_cache_miss(key: str) -> None:
    cache_misses.add(1, {"cache.endpoint": cache_endpoint_from_key(key)})


def record_operation(operation: str, duration_ms: float, *, success: bool = True) -> None:
    attrs = {"cache.operation": operation, "cache.success": success}
    operation_duration.record(duration_ms, attrs)
    if not success:
        operation_errors.add(1, {"cache.operation": operation})


@contextmanager
def trace_cache_operation(operation: str, key: str = "") -> Iterator[None]:
    attrs: dict[str, str] = {"cache.operation": operation}
    if key:
        attrs["cache.key"] = key[:128]
        attrs["cache.endpoint"] = cache_endpoint_from_key(key)
    with _tracer.start_as_current_span(f"cache.{operation}", attributes=attrs):
        yield


def _pool_observations() -> Iterator[Observation]:
    from app.cache.redis_client import get_redis

    client = get_redis()
    if client is None:
        yield Observation(0, {"pool.metric": "max_connections"})
        yield Observation(0, {"pool.metric": "available"})
        yield Observation(0, {"pool.metric": "in_use"})
        return

    pool = client.connection_pool
    max_connections = int(getattr(pool, "max_connections", 0) or 0)
    available = len(getattr(pool, "_available_connections", []))
    in_use = len(getattr(pool, "_in_use_connections", []))
    yield Observation(max_connections, {"pool.metric": "max_connections"})
    yield Observation(available, {"pool.metric": "available"})
    yield Observation(in_use, {"pool.metric": "in_use"})


def register_pool_metrics() -> None:
    global _pool_gauge_registered
    if _pool_gauge_registered:
        return
    _meter.create_observable_gauge(
        "wkpoule.redis.pool.connections",
        callbacks=[lambda _options: _pool_observations()],
        description="Redis connection pool usage",
    )
    _pool_gauge_registered = True


def reset_pool_metrics_for_tests() -> None:
    global _pool_gauge_registered
    _pool_gauge_registered = False


class TimedCacheOperation:
    """Context manager: span + latency histogram for a cache operation."""

    def __init__(self, operation: str, key: str = "") -> None:
        self._operation = operation
        self._key = key
        self._start = 0.0
        self._success = True
        self._span_cm = trace_cache_operation(operation, key)

    def __enter__(self) -> TimedCacheOperation:
        self._start = time.perf_counter()
        self._span_cm.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self._success = False
        duration_ms = (time.perf_counter() - self._start) * 1000
        record_operation(self._operation, duration_ms, success=self._success)
        return self._span_cm.__exit__(exc_type, exc, tb)

    async def __aenter__(self) -> TimedCacheOperation:
        self._start = time.perf_counter()
        self._span_cm.__enter__()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self._success = False
        duration_ms = (time.perf_counter() - self._start) * 1000
        record_operation(self._operation, duration_ms, success=self._success)
        self._span_cm.__exit__(exc_type, exc, tb)
