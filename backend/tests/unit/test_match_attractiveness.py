"""Unit tests for venue fixture attractiveness scoring."""

from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.match_attractiveness import (
    attractiveness_blend,
    blend_to_stars,
    compute_attractiveness_stars,
)


def _match(stage: str, home_rank: int | None, away_rank: int | None):
    return SimpleNamespace(
        stage=stage,
        home_team=SimpleNamespace(world_ranking=home_rank),
        away_team=SimpleNamespace(world_ranking=away_rank),
    )


def test_blend_to_stars_maps_thresholds():
    assert blend_to_stars(80.0) == 5
    assert blend_to_stars(60.0) == 4
    assert blend_to_stars(45.0) == 3
    assert blend_to_stars(30.0) == 2
    assert blend_to_stars(10.0) == 1


def test_attractiveness_blend_uses_rankings_for_group_stage():
    match = _match("group", 5, 20)

    assert attractiveness_blend(match) > 40.0


def test_compute_attractiveness_stars_uses_knockout_floor():
    final = _match("final", None, None)
    group = _match("group", 1, 2)

    assert compute_attractiveness_stars(final) == 5
    assert compute_attractiveness_stars(group) >= 3
