"""Validation and bracket resolution for knockout advance picks on draws."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.match import Match
from app.services.match_stages import is_knockout_stage


def resolve_fixture_team_ids(
    db: Session,
    match: Match,
    user_id: int,
) -> tuple[int | None, int | None]:
    """DB team ids, or knockout participants inferred from this user's earlier tips."""
    if match.home_team_id is not None and match.away_team_id is not None:
        return match.home_team_id, match.away_team_id
    if not is_knockout_stage(match.stage) or match.match_number < 73:
        return match.home_team_id, match.away_team_id
    from app.services.bracket_resolver import compute_predicted_knockout_teams

    predicted_map, _ = compute_predicted_knockout_teams(db, user_id)
    pair = predicted_map.get(match.match_number)
    if not pair:
        return None, None
    home, away = pair
    return (
        home.id if home is not None else None,
        away.id if away is not None else None,
    )


def validate_advance_team_for_prediction(
    match: Match,
    home_score: int,
    away_score: int,
    advance_team_id: int | None,
    *,
    home_team_id: int | None = None,
    away_team_id: int | None = None,
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

    resolved_home = home_team_id if home_team_id is not None else match.home_team_id
    resolved_away = away_team_id if away_team_id is not None else match.away_team_id
    if resolved_home is None or resolved_away is None:
        raise HTTPException(
            status_code=400,
            detail="Teams must be known before predicting a knockout draw",
        )

    allowed = {resolved_home, resolved_away}
    if advance_team_id is None or advance_team_id not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Choose which team advances after a predicted draw",
        )
    return advance_team_id
