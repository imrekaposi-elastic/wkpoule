from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TeamOut(BaseModel):
    id: int
    name: str
    fifa_code: str
    group_letter: str
    world_ranking: int
    flag_url: str

    model_config = {"from_attributes": True}


class VenueOut(BaseModel):
    id: int
    name: str
    city: str
    country: str
    capacity: int

    model_config = {"from_attributes": True}


class VenueScheduledMatchOut(BaseModel):
    """Match row for the venues schedule (no auth-specific prediction fill-ins)."""

    match_id: int
    match_number: int
    stage: str
    group_letter: str | None = None
    kickoff_utc: datetime
    home_team_name: str | None = None
    away_team_name: str | None = None
    home_team_code: str | None = None
    away_team_code: str | None = None
    attractiveness_stars: int = Field(ge=1, le=5)


class VenueDetailOut(BaseModel):
    id: int
    name: str
    city: str
    country: str
    capacity: int
    latitude: float
    longitude: float
    year_built: int | None = None
    image_url: str | None = None
    rating: int | None = None
    review_en: str | None = None
    review_nl: str | None = None
    review_pt: str | None = None
    review_de: str | None = None
    review_he: str | None = None
    expected_temp_celsius: float | None = None
    city_attractiveness: int | None = None
    accessibility_en: str | None = None
    accessibility_nl: str | None = None
    accessibility_pt: str | None = None
    accessibility_de: str | None = None
    accessibility_he: str | None = None
    matches: list[VenueScheduledMatchOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class FunCommentOut(BaseModel):
    comment_text: str
    comment_text_nl: str | None = None
    comment_text_pt: str | None = None
    comment_text_de: str | None = None
    comment_text_it: str | None = None
    comment_text_es: str | None = None
    style: str

    model_config = {"from_attributes": True}


class ExpertPrediction(BaseModel):
    home_goals: int
    away_goals: int
    label: str


class MatchOut(BaseModel):
    id: int
    match_number: int
    stage: str
    group_letter: str | None
    home_team: TeamOut | None
    away_team: TeamOut | None
    bracket_home_slot: str | None = Field(None, description="FIFA-style slot for home side, e.g. E1")
    bracket_away_slot: str | None = Field(None, description="FIFA-style slot for away side, e.g. F3")
    venue: VenueOut
    kickoff_utc: datetime
    home_score: int | None
    away_score: int | None
    status: str
    fun_comment: FunCommentOut | None = None
    temperature_celsius: float | None = None
    expert_prediction: ExpertPrediction | None = None
    prediction_editable: bool = Field(
        ...,
        description="True if the current user may submit or change a score prediction for this match",
    )

    model_config = {"from_attributes": True}


class ScoreUpdate(BaseModel):
    home_score: int = Field(ge=0, le=30)
    away_score: int = Field(ge=0, le=30)
    status: Literal["upcoming", "in_progress", "completed"] = "completed"
