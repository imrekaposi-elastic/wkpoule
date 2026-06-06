"""Record user conversion milestones (predictions, subgroup chat) for analytics."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import distinct, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.match import Match
from app.models.prediction import Prediction
from app.models.subgroup import SubgroupMessage
from app.models.user import User
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

PREDICTION_MILESTONE_CHECKS: list[tuple[str, Callable[[Session, int], bool]]] = [
    ("first_prediction", lambda db, user_id: _user_has_any_prediction(db, user_id)),
    *[
        (key, lambda db, user_id, stages=stages: _user_has_all_predictions_for_stages(db, user_id, stages))
        for key, stages in MILESTONE_STAGE_GROUPS
    ],
    ("tournament_complete", lambda db, user_id: _user_has_all_predictions(db, user_id)),
]

SUBGROUP_MESSAGE_MILESTONE_KEY = "subgroup_message_posted"


def _user_has_any_prediction(db: Session, user_id: int) -> bool:
    n_preds = (
        db.query(func.count(Prediction.id))
        .filter(Prediction.user_id == user_id)
        .scalar()
    )
    return int(n_preds or 0) >= 1


def _user_has_all_predictions(db: Session, user_id: int) -> bool:
    n_matches = db.query(func.count(Match.id)).scalar()
    if not n_matches:
        return False
    n_preds = (
        db.query(func.count(Prediction.id))
        .filter(Prediction.user_id == user_id)
        .scalar()
    )
    return int(n_preds or 0) >= int(n_matches)


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


def _existing_milestone_keys(db: Session, user_id: int) -> set[str]:
    return {
        row[0]
        for row in db.query(UserPredictionMilestone.milestone_key)
        .filter(UserPredictionMilestone.user_id == user_id)
        .all()
    }


def log_milestone_achieved(
    user_id: int,
    milestone_key: str,
    *,
    username: str | None = None,
    **context: object,
) -> None:
    extra: dict[str, object] = {
        "event.action": "milestone_achieved",
        "event.category": "application",
        "event.outcome": "success",
        "event.type": "info",
        "milestone.key": milestone_key,
        "user.id": user_id,
    }
    if username:
        extra["user.name"] = username
    extra.update(context)
    logger.info("milestone achieved: %s", milestone_key, extra=extra)


def _record_milestone_keys(
    db: Session,
    user_id: int,
    checks: list[tuple[str, Callable[[Session, int], bool]]],
    *,
    username: str | None = None,
) -> list[str]:
    existing = _existing_milestone_keys(db, user_id)
    newly: list[str] = []
    now = datetime.now(timezone.utc)
    for key, check in checks:
        if key in existing:
            continue
        if not check(db, user_id):
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
            logger.warning(
                "milestone insert race for user %s (keys=%s)",
                user_id,
                newly,
                extra={
                    "event.action": "milestone_achieved",
                    "event.outcome": "failure",
                    "user.id": user_id,
                    "milestone.keys": newly,
                },
            )
            return []
        for key in newly:
            log_milestone_achieved(user_id, key, username=username)
    return newly


def record_new_milestones(
    db: Session,
    user_id: int,
    *,
    username: str | None = None,
) -> list[str]:
    """
    Insert rows for any milestones the user just reached (idempotent per user+milestone).
    Returns milestone_key values newly stored (for API responses / RUM conversion goals).
    """
    return _record_milestone_keys(
        db,
        user_id,
        PREDICTION_MILESTONE_CHECKS,
        username=username,
    )


def record_subgroup_message_milestone(
    db: Session,
    user_id: int,
    *,
    username: str | None = None,
    subgroup_id: int | None = None,
    message_id: int | None = None,
) -> list[str]:
    """
    Record every subgroup chat post as a conversion milestone (log + RUM).
    The first post is also stored in user_prediction_milestones for /milestones.
    """
    has_message = (
        int(
            db.query(func.count(SubgroupMessage.id))
            .filter(SubgroupMessage.user_id == user_id)
            .scalar()
            or 0
        )
        >= 1
    )
    if not has_message:
        return []

    log_context: dict[str, object] = {}
    if subgroup_id is not None:
        log_context["subgroup.id"] = subgroup_id
    if message_id is not None:
        log_context["subgroup.message.id"] = message_id

    if SUBGROUP_MESSAGE_MILESTONE_KEY not in _existing_milestone_keys(db, user_id):
        now = datetime.now(timezone.utc)
        db.add(
            UserPredictionMilestone(
                user_id=user_id,
                milestone_key=SUBGROUP_MESSAGE_MILESTONE_KEY,
                achieved_at=now,
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()

    log_milestone_achieved(
        user_id,
        SUBGROUP_MESSAGE_MILESTONE_KEY,
        username=username,
        **log_context,
    )
    return [SUBGROUP_MESSAGE_MILESTONE_KEY]


def list_milestones_for_user(db: Session, user_id: int) -> list[UserPredictionMilestone]:
    return (
        db.query(UserPredictionMilestone)
        .filter(UserPredictionMilestone.user_id == user_id)
        .order_by(UserPredictionMilestone.achieved_at)
        .all()
    )


def backfill_milestones_for_existing_users() -> None:
    """
    Idempotent startup backfill for users who already qualified before milestone tracking shipped.
    Does not emit RUM events (browser-only); writes DB rows and structured logs for new rows.
    """
    db = SessionLocal()
    try:
        pred_user_ids = {
            row[0] for row in db.query(distinct(Prediction.user_id)).all() if row[0] is not None
        }
        msg_user_ids = {
            row[0]
            for row in db.query(distinct(SubgroupMessage.user_id)).all()
            if row[0] is not None
        }
        for user_id in pred_user_ids | msg_user_ids:
            user = db.get(User, user_id)
            username = user.username if user is not None else None
            if user_id in pred_user_ids:
                record_new_milestones(db, user_id, username=username)
            if user_id in msg_user_ids:
                record_subgroup_message_milestone(db, user_id, username=username)
    except Exception:
        logger.exception("Milestone backfill failed")
    finally:
        db.close()
