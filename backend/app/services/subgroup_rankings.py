"""Participant rankings for all users or a restricted set (e.g. subgroup members)."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.ranking import ParticipantRanking
from app.services.scoring import calculate_points


def compute_participant_rankings(
    db: Session,
    user_ids: list[int] | None = None,
) -> list[ParticipantRanking]:
    """
    If user_ids is None, rank all users. Otherwise only users in user_ids (must exist).
    """
    q = db.query(User).filter(User.is_admin.is_(False))
    if user_ids is not None:
        if not user_ids:
            return []
        q = q.filter(User.id.in_(user_ids))
    users = q.all()

    completed_matches = (
        db.query(Match)
        .filter(Match.status == "completed", Match.home_score.isnot(None))
        .all()
    )
    match_scores = {m.id: (m.home_score, m.away_score) for m in completed_matches}

    scored_predictions = (
        db.query(Prediction)
        .filter(Prediction.match_id.in_(match_scores.keys()))
        .all()
    ) if match_scores else []

    pred_by_user: dict[int, list[Prediction]] = {}
    for p in scored_predictions:
        if user_ids is not None and p.user_id not in user_ids:
            continue
        pred_by_user.setdefault(p.user_id, []).append(p)

    total_preds_by_user: dict[int, int] = {}
    pred_count_q = db.query(Prediction.user_id, func.count()).group_by(Prediction.user_id)
    if user_ids is not None:
        pred_count_q = pred_count_q.filter(Prediction.user_id.in_(user_ids))
    for row in pred_count_q.all():
        total_preds_by_user[row[0]] = row[1]

    rankings: list[ParticipantRanking] = []
    for u in users:
        total = 0
        correct_results = 0
        correct_scores = 0
        correct_goals = 0
        for p in pred_by_user.get(u.id, []):
            if p.points is not None:
                pts = p.points
            else:
                actual = match_scores[p.match_id]
                pts = calculate_points(p.home_score, p.away_score, actual[0], actual[1])["points"]
            total += pts

            actual = match_scores[p.match_id]
            result = calculate_points(p.home_score, p.away_score, actual[0], actual[1])
            if result["correct_result"]:
                correct_results += 1
            if result["correct_score"]:
                correct_scores += 1
            if result["correct_goal_count"]:
                correct_goals += 1

        rankings.append(
            ParticipantRanking(
                rank=0,
                user_id=u.id,
                username=u.username,
                total_points=total,
                correct_results=correct_results,
                correct_scores=correct_scores,
                correct_goal_counts=correct_goals,
                predictions_made=total_preds_by_user.get(u.id, 0),
            )
        )

    rankings.sort(key=lambda r: r.total_points, reverse=True)
    for i, r in enumerate(rankings):
        r.rank = i + 1
    return rankings
