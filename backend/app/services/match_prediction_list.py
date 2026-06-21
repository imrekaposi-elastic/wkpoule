"""Shared helpers for listing non-admin match predictions."""

from __future__ import annotations

from typing import Literal

from sqlalchemy.orm import Session, joinedload

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import MatchPredictionListItem
from app.services.scoring import calculate_prediction_points

PredictionOutcome = Literal["home_win", "away_win", "draw"]

OUTCOME_PAGE_SIZE = 10


def prediction_outcome(home_score: int, away_score: int) -> PredictionOutcome:
    if home_score > away_score:
        return "home_win"
    if away_score > home_score:
        return "away_win"
    return "draw"


def non_admin_predictions_for_match(db: Session, match_id: int) -> list[Prediction]:
    return (
        db.query(Prediction)
        .join(Prediction.user)
        .filter(Prediction.match_id == match_id, User.is_admin.is_(False))
        .options(joinedload(Prediction.user))
        .order_by(Prediction.updated_at.desc())
        .all()
    )


def to_list_item(pred: Prediction, match: Match) -> MatchPredictionListItem:
    pts = None
    if match.status == "completed" and match.home_score is not None:
        pts = calculate_prediction_points(pred, match)["points"]
    return MatchPredictionListItem(
        user_id=pred.user_id,
        username=pred.user.username,
        home_score=pred.home_score,
        away_score=pred.away_score,
        advance_team_id=pred.advance_team_id,
        points=pts,
    )


def summary_counts(predictions: list[Prediction]) -> dict[str, int]:
    counts = {"home_win": 0, "away_win": 0, "draw": 0}
    for pred in predictions:
        counts[prediction_outcome(pred.home_score, pred.away_score)] += 1
    return counts


def predictions_for_outcome(
    predictions: list[Prediction], outcome: PredictionOutcome
) -> list[Prediction]:
    return [
        p
        for p in predictions
        if prediction_outcome(p.home_score, p.away_score) == outcome
    ]
