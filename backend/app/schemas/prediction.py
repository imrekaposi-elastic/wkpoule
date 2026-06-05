from datetime import datetime

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    home_score: int = Field(ge=0, le=20)
    away_score: int = Field(ge=0, le=20)
    advance_team_id: int | None = None


class PredictionOut(BaseModel):
    id: int
    user_id: int
    username: str
    match_id: int
    home_score: int
    away_score: int
    advance_team_id: int | None = None
    points: int | None = None
    created_at: datetime
    updated_at: datetime
    newly_achieved: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class MyPredictionBrief(BaseModel):
    """Lightweight tip for match list overlays (all user tips, not paginated)."""

    match_id: int
    home_score: int
    away_score: int
    advance_team_id: int | None = None


class MyPredictionOut(BaseModel):
    match_id: int
    match_number: int
    home_team: str | None
    away_team: str | None
    home_team_code: str | None = None
    away_team_code: str | None = None
    home_score: int
    away_score: int
    points: int | None = None
    match_status: str

    model_config = {"from_attributes": True}


class MatchPredictionSummaryOut(BaseModel):
    total: int
    home_win_count: int
    away_win_count: int
    draw_count: int


class MatchPredictionListItem(BaseModel):
    user_id: int
    username: str
    home_score: int
    away_score: int
    advance_team_id: int | None = None
    points: int | None = None
