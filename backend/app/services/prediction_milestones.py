"""Record when a user has tipped every match in a phase (group, knock-out rounds, finals)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.user_prediction_milestone import UserPredictionMilestone

logger = logging.getLogger(__name__)

# (milestone_key, match.stage values included in that milestone)
MILESTONE_STAGE_GROUPS: list[tuple[str, tuple[str, ...]]] = [
    ("group_complete", ("group",)),
    ("round_of_32_complete", ("round_of_32",)),
    ("round_of_16_complete", ("round_of_16",)),
    ("quarter_final_complete", ("quarter_final",)),
    ("semi_final_complete", ("semi_final",)),
    ("finals_complete", ("third_place", "final")),
]


def _user_has_all_predictions_for_stages(
    db: Session, user_id: int, stages: tuple[str, ...]
) -> bool:
    match_ids = [
        row[0]
        for row in db.query(Match.id).filter(Match.stage.in_(stages)).all()
    ]
    n_matches = len(match_ids)
    if n_matches == 0:
        return False
    n_preds = (
        db.query(func.count(Prediction.id))
        .filter(Prediction.user_id == user_id, Prediction.match_id.in_(match_ids))
        .scalar()
    )
    return int(n_preds or 0) >= n_matches


def record_new_milestones(db: Session, user_id: int) -> list[str]:
    """
    Insert rows for any phase the user just completed (idempotent per user+milestone).
    Returns milestone_key values newly stored (for logs / future metrics).
    """
    existing = {
        row[0]
        for row in db.query(UserPredictionMilestone.milestone_key)
        .filter(UserPredictionMilestone.user_id == user_id)
        .all()
    }
    newly: list[str] = []
    now = datetime.now(timezone.utc)
    for key, stages in MILESTONE_STAGE_GROUPS:
        if key in existing:
            continue
        if not _user_has_all_predictions_for_stages(db, user_id, stages):
            continue
        db.add(
            UserPredictionMilestone(
                user_id=user_id,
                milestone_key=key,
                achieved_at=now,
            )
        )
        newly.append(key)
    if newly:
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return []
        for k in newly:
            logger.info("prediction_milestone user_id=%s milestone=%s", user_id, k)
    return newly


def list_milestones_for_user(db: Session, user_id: int) -> list[UserPredictionMilestone]:
    return (
        db.query(UserPredictionMilestone)
        .filter(UserPredictionMilestone.user_id == user_id)
        .order_by(UserPredictionMilestone.achieved_at)
        .all()
    )
