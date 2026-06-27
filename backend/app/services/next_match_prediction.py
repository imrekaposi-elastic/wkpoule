"""Find the next upcoming match that still needs a user prediction."""

from sqlalchemy.orm import Session, joinedload

from app.models.match import Match
from app.models.prediction import Prediction
from app.services.prediction_lock import match_accepts_prediction_updates


def first_match_needing_prediction(
    db: Session,
    user_id: int,
    *,
    stage: str | None = None,
    after_match_number: int | None = None,
) -> Match | None:
    predicted_ids = {
        row[0]
        for row in db.query(Prediction.match_id)
        .filter(Prediction.user_id == user_id)
        .all()
    }
    q = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
            joinedload(Match.fun_comment),
        )
        .filter(Match.status == "upcoming")
    )
    if stage:
        q = q.filter(Match.stage == stage)
    if after_match_number is not None:
        q = q.filter(Match.match_number > after_match_number)
    matches = q.order_by(Match.match_number).all()
    for m in matches:
        if m.id in predicted_ids:
            continue
        if match_accepts_prediction_updates(m):
            return m
    return None
