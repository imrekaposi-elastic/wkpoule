"""Unit tests for cache OpenTelemetry metrics helpers."""

from app.cache.metrics import cache_endpoint_from_key, record_cache_hit, record_cache_miss


def test_cache_endpoint_from_key():
    assert cache_endpoint_from_key("wkpoule:rankings:page=1:size=20") == "rankings"
    assert cache_endpoint_from_key("wkpoule:matches:detail:id=1") == "matches"
    assert cache_endpoint_from_key("other") == "unknown"


def test_record_cache_hit_and_miss_do_not_raise():
    record_cache_hit("wkpoule:teams:list")
    record_cache_miss("wkpoule:teams:list")
