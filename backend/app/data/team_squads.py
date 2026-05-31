"""Real national-team squads from official announcements (May 2026)."""

from __future__ import annotations

from app.data.team_squad_overrides import TEAM_SQUAD_OVERRIDES
from app.data.team_squads_data import TEAM_SQUADS

_SQUAD_PLAYER_KEYS = ("name", "position", "shirt_number", "club", "caps", "sort_order")


def _normalize_player(player: dict) -> dict:
    return {key: player[key] for key in _SQUAD_PLAYER_KEYS}


def build_team_squad(
    fifa_code: str,
    team_name: str,
    world_ranking: int,
) -> list[dict]:
    """Return announced squad players for a team."""
    del team_name, world_ranking
    code = fifa_code.upper()
    if code in TEAM_SQUAD_OVERRIDES:
        return [_normalize_player(player) for player in TEAM_SQUAD_OVERRIDES[code]]
    squad = TEAM_SQUADS.get(code)
    if squad:
        return [_normalize_player(player) for player in squad]
    return []
