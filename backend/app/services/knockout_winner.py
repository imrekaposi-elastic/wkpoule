"""Resolve knockout winner from predicted scores (no bracket graph imports)."""

from app.models.team import Team


def predicted_winner_team_id(
    home_id: int,
    away_id: int,
    home_score: int,
    away_score: int,
    teams_by_id: dict[int, Team],
    advance_team_id: int | None,
) -> int:
    if home_score > away_score:
        return home_id
    if home_score < away_score:
        return away_id
    if advance_team_id is not None:
        return advance_team_id
    th, ta = teams_by_id[home_id], teams_by_id[away_id]
    return home_id if th.world_ranking <= ta.world_ranking else away_id
