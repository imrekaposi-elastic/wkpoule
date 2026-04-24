"""Heuristic 'fixture hype' score (1–5 stars) for venue schedules."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.match import Match

# Knockout (after group): no FIFA-rank blend — fixed hype floor 3★.
KNOCKOUT_STARS: dict[str, int] = {
    "round_of_32": 3,
    "round_of_16": 3,
    "quarter_final": 4,
    "semi_final": 4,
    "third_place": 4,
    "final": 5,
}

# Group stage only: blend stage weight with team rankings.
STAGE_SCORE: dict[str, float] = {
    "group": 14.0,
    "round_of_32": 32.0,
    "round_of_16": 44.0,
    "quarter_final": 56.0,
    "semi_final": 70.0,
    "third_place": 60.0,
    "final": 86.0,
}


def _rank_points(world_ranking: int | None) -> float:
    """Higher = more exciting on paper (top FIFA ranks score high). Unknown/TBD ranks low."""
    if world_ranking is None or world_ranking <= 0:
        return 20.0
    return max(5.0, 101.0 - min(world_ranking, 100))


def attractiveness_blend(match: Match) -> float:
    hp = _rank_points(match.home_team.world_ranking if match.home_team else None)
    ap = _rank_points(match.away_team.world_ranking if match.away_team else None)
    team_part = (hp + ap) / 2.0
    st = STAGE_SCORE.get(match.stage, 16.0)
    return 0.38 * st + 0.62 * team_part


def blend_to_stars(blend: float) -> int:
    if blend >= 74.0:
        return 5
    if blend >= 58.0:
        return 4
    if blend >= 42.0:
        return 3
    if blend >= 28.0:
        return 2
    return 1


def compute_attractiveness_stars(match: Match) -> int:
    if match.stage != "group":
        return max(3, KNOCKOUT_STARS.get(match.stage, 3))
    return blend_to_stars(attractiveness_blend(match))
