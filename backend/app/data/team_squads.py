"""Real national-team squads from official announcements (May 2026)."""

from __future__ import annotations

from app.data.player_physical import apply_physical_data
from app.data.team_squad_overrides import TEAM_SQUAD_OVERRIDES
from app.data.team_squads_data import TEAM_SQUADS


def _normalize_player(player: dict) -> dict:
    merged = apply_physical_data(dict(player))
    normalized = {
        "name": merged["name"],
        "position": merged["position"],
        "shirt_number": merged["shirt_number"],
        "club": merged["club"],
        "caps": merged.get("caps", 0),
        "sort_order": merged.get("sort_order", 0),
        "height_cm": int(merged.get("height_cm") or 0),
        "weight_kg": int(merged.get("weight_kg") or 0),
    }
    dob = merged.get("date_of_birth")
    age = merged.get("age")
    if dob is not None:
        normalized["date_of_birth"] = dob
    if age is not None:
        normalized["age"] = age
    return normalized


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
