"""Validation and bracket resolution for knockout advance picks on draws."""

from __future__ import annotations

from fastapi import HTTPException

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.team import Team
from app.services.match_stages import is_knockout_stage


def validate_advance_team_for_prediction(
    match: Match,
    home_score: int,
    away_score: int,
    advance_team_id: int | None,
) -> int | None:
    """Return normalized advance_team_id or raise HTTP 400."""
    if not is_knockout_stage(match.stage):
        if advance_team_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Advance team is only used for knockout matches",
            )
        return None

    if home_score != away_score:
        if advance_team_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Advance team is only required for a predicted draw",
            )
        return None

    if match.home_team_id is None or match.away_team_id is None:
        raise HTTPException(
            status_code=400,
            detail="Teams must be known before predicting a knockout draw",
        )

    allowed = {match.home_team_id, match.away_team_id}
    if advance_team_id is None or advance_team_id not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Choose which team advances after a predicted draw",
        )
    return advance_team_id


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
