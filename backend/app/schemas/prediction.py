from datetime import datetime

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    home_score: int = Field(ge=0, le=20)
    away_score: int = Field(ge=0, le=20)


class PredictionOut(BaseModel):
    id: int
    user_id: int
    username: str
    match_id: int
    home_score: int
    away_score: int
    points: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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
