"""Real national-team squads from official announcements (May 2026)."""

from __future__ import annotations

from app.data.player_physical import apply_physical_data
from app.data.team_squad_overrides import TEAM_SQUAD_OVERRIDES
from app.data.team_squads_data import TEAM_SQUADS


def _normalize_player(player: dict) -> dict:
    merged = dict(player)
    height = merged.get("height_cm") or None
    weight = merged.get("weight_kg") or None
    if height == 0:
        height = None
    if weight == 0:
        weight = None
    merged["height_cm"] = height
    merged["weight_kg"] = weight
    return apply_physical_data(merged)


def build_team_squad(
    fifa_code: str,
    team_name: str,
    world_ranking: int,
) -> list[dict]:
    """Return announced squad players for a team."""
    code = fifa_code.upper()
    if code in TEAM_SQUAD_OVERRIDES:
        return [_normalize_player(player) for player in TEAM_SQUAD_OVERRIDES[code]]
    squad = TEAM_SQUADS.get(code)
    if squad:
        return [_normalize_player(player) for player in squad]
    return []
