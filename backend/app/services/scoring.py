import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.match import Match
from app.models.prediction import Prediction
from app.services.match_stages import is_knockout_stage

logger = logging.getLogger("wkpoule.scoring")


def resolve_winner_team_id(
    home_team_id: int | None,
    away_team_id: int | None,
    home_score: int,
    away_score: int,
    winner_team_id: int | None = None,
) -> int | None:
    """Match winner after 90 minutes, or stored winner when level at full time."""
    if home_score > away_score:
        return home_team_id
    if away_score > home_score:
        return away_team_id
    return winner_team_id


def calculate_points(
    pred_home: int,
    pred_away: int,
    actual_home: int,
    actual_away: int,
    *,
    is_knockout: bool = False,
    pred_advance_team_id: int | None = None,
    actual_winner_team_id: int | None = None,
) -> dict:
    """Score a tip against the official result after 90 minutes."""
    if is_knockout and actual_home == actual_away:
        return _knockout_draw_after_90_points(
            pred_home,
            pred_away,
            actual_home,
            actual_away,
            pred_advance_team_id,
            actual_winner_team_id,
        )
    return _standard_points(pred_home, pred_away, actual_home, actual_away)


def calculate_prediction_points(pred: Prediction, match: Match) -> dict:
    """Score one stored prediction against a completed match."""
    return calculate_points(
        pred.home_score,
        pred.away_score,
        match.home_score,
        match.away_score,
        is_knockout=is_knockout_stage(match.stage),
        pred_advance_team_id=pred.advance_team_id,
        actual_winner_team_id=resolve_winner_team_id(
            match.home_team_id,
            match.away_team_id,
            match.home_score,
            match.away_score,
            match.winner_team_id,
        ),
    )


def _standard_points(
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


def _knockout_draw_after_90_points(
    pred_home: int,
    pred_away: int,
    actual_home: int,
    actual_away: int,
    pred_advance_team_id: int | None,
    actual_winner_team_id: int | None,
) -> dict:
    """Knockout edge case: actual score is level after 90 minutes.

    Points: up to 8 (exact score) + 1 (goal count) + 3 (correct winner pick).
    The usual draw-as-outcome bonus does not apply.
    """
    points = 0
    correct_result = False
    correct_score = False
    correct_goal_count = False

    if pred_home == actual_home and pred_away == actual_away:
        correct_score = True
        points += 8

    if (pred_home + pred_away) == (actual_home + actual_away):
        correct_goal_count = True
        points += 1

    if (
        actual_winner_team_id is not None
        and pred_advance_team_id is not None
        and pred_advance_team_id == actual_winner_team_id
    ):
        correct_result = True
        points += 3

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

        if not completed_matches:
            return 0

        match_by_id = {m.id: m for m in completed_matches}

        predictions = (
            db.query(Prediction)
            .filter(Prediction.match_id.in_(match_by_id.keys()))
            .all()
        )

        for pred in predictions:
            match = match_by_id[pred.match_id]
            result = calculate_prediction_points(pred, match)
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
