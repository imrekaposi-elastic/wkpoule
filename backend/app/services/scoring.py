import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.match import Match
from app.models.prediction import Prediction

logger = logging.getLogger("wkpoule.scoring")


def calculate_points(
    pred_home: int, pred_away: int, actual_home: int, actual_away: int
) -> dict:
    points = 0
    correct_result = False
    correct_score = False
    correct_goal_count = False

    pred_outcome = _outcome(pred_home, pred_away)
    actual_outcome = _outcome(actual_home, actual_away)
    if pred_outcome == actual_outcome:
        correct_result = True
        points += 3

    if pred_home == actual_home and pred_away == actual_away:
        correct_score = True
        points += 8

    if (pred_home + pred_away) == (actual_home + actual_away):
        correct_goal_count = True
        points += 1

    return {
        "points": points,
        "correct_result": correct_result,
        "correct_score": correct_score,
        "correct_goal_count": correct_goal_count,
    }


def _outcome(home: int, away: int) -> str:
    if home > away:
        return "home"
    elif home < away:
        return "away"
    return "draw"


def recalculate_points() -> int:
    """Recalculate and persist points for all predictions on completed matches.

    Returns the number of predictions that were updated.
    """
    db: Session = SessionLocal()
    updated = 0
    try:
        completed_matches = (
            db.query(Match)
            .filter(
                Match.status == "completed",
                Match.home_score.isnot(None),
                Match.away_score.isnot(None),
            )
            .all()
        )

        match_scores = {m.id: (m.home_score, m.away_score) for m in completed_matches}
        if not match_scores:
            return 0

        predictions = (
            db.query(Prediction)
            .filter(Prediction.match_id.in_(match_scores.keys()))
            .all()
        )

        for pred in predictions:
            actual_home, actual_away = match_scores[pred.match_id]
            result = calculate_points(
                pred.home_score, pred.away_score, actual_home, actual_away
            )
            new_points = result["points"]
            if pred.points != new_points:
                pred.points = new_points
                updated += 1

        if updated > 0:
            db.commit()
            logger.info("Recalculated points: %d prediction(s) updated", updated)
    except Exception:
        db.rollback()
        logger.exception("Error recalculating points")
    finally:
        db.close()

    return updated
