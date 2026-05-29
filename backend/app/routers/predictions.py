import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.database import get_db
from app.models.match import Match
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.pagination import DEFAULT_PAGE_SIZE, PaginatedResponse, paginate_list
from app.schemas.prediction import (
    MyPredictionBrief,
    MyPredictionOut,
    PredictionOut,
    PredictionRequest,
)
from app.schemas.prediction_milestone import PredictionMilestoneOut
from app.schemas.ranking import VirtualGroupTable
from app.services.prediction_advance import (
    resolve_fixture_team_ids,
    validate_advance_team_for_prediction,
)
from app.services.prediction_lock import match_accepts_prediction_updates
from app.services.prediction_milestones import list_milestones_for_user, record_new_milestones
from app.services.scoring import calculate_points
from app.services.virtual_standings import (
    best_third_place_team_ids,
    compute_virtual_group_standings,
    third_place_qualifies_for_group,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/milestones", response_model=list[PredictionMilestoneOut])
def my_prediction_milestones(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Phases for which this user has submitted a tip for every match (group → finals)."""
    return list_milestones_for_user(db, user.id)


@router.put("/{match_id}", response_model=PredictionOut)
def upsert_prediction(
    match_id: int,
    body: PredictionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status != "upcoming":
        raise HTTPException(status_code=400, detail="Predictions are locked for this match")
    if not match_accepts_prediction_updates(match):
        raise HTTPException(
            status_code=400,
            detail="Predictions cannot be changed within 30 minutes of kickoff",
        )

    home_tid, away_tid = resolve_fixture_team_ids(db, match, user.id)
    advance_team_id = validate_advance_team_for_prediction(
        match,
        body.home_score,
        body.away_score,
        body.advance_team_id,
        home_team_id=home_tid,
        away_team_id=away_tid,
    )

    pred = (
        db.query(Prediction)
        .filter(Prediction.user_id == user.id, Prediction.match_id == match_id)
        .first()
    )
    is_update = pred is not None
    if pred:
        pred.home_score = body.home_score
        pred.away_score = body.away_score
        pred.advance_team_id = advance_team_id
    else:
        pred = Prediction(
            user_id=user.id,
            match_id=match_id,
            home_score=body.home_score,
            away_score=body.away_score,
            advance_team_id=advance_team_id,
        )
        db.add(pred)
    db.commit()
    db.refresh(pred)
    record_new_milestones(db, user.id)
    logger.info(
        "%s %s prediction for match %s",
        user.username,
        "updated" if is_update else "created",
        match.match_number,
        extra={
            "event.action": "prediction_upsert",
            "event.category": "application",
            "event.outcome": "success",
            "event.type": "change",
            "user.name": user.username,
            "user.id": user.id,
            "match.id": match_id,
            "match.number": match.match_number,
            "prediction.home_score": body.home_score,
            "prediction.away_score": body.away_score,
            "prediction.advance_team_id": advance_team_id,
            "prediction.is_update": is_update,
        },
    )

    return PredictionOut(
        id=pred.id,
        user_id=pred.user_id,
        username=user.username,
        match_id=pred.match_id,
        home_score=pred.home_score,
        away_score=pred.away_score,
        advance_team_id=pred.advance_team_id,
        points=None,
        created_at=pred.created_at,
        updated_at=pred.updated_at,
    )


@router.get("/virtual-groups", response_model=list[VirtualGroupTable])
def virtual_groups(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Group tables based on this user's predicted scores only (predicted matches count)."""
    tables = compute_virtual_group_standings(db, user.id)
    best_third_ids = best_third_place_team_ids(tables)
    result: list[VirtualGroupTable] = []
    for gt in tables:
        result.append(
            VirtualGroupTable(
                group_letter=gt.group_letter,
                standings=gt.standings,
                third_place_qualifies=third_place_qualifies_for_group(gt, best_third_ids),
            )
        )
    return result


@router.get("/mine/brief", response_model=list[MyPredictionBrief])
def my_predictions_brief(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """All user tips (scores only) for match list overlays — max one row per fixture."""
    rows = (
        db.query(
            Prediction.match_id,
            Prediction.home_score,
            Prediction.away_score,
            Prediction.advance_team_id,
        )
        .filter(Prediction.user_id == user.id)
        .all()
    )
    return [
        MyPredictionBrief(
            match_id=mid,
            home_score=h,
            away_score=a,
            advance_team_id=adv,
        )
        for mid, h, a, adv in rows
    ]


@router.get("/mine", response_model=PaginatedResponse[MyPredictionOut])
def my_predictions(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=20),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preds = (
        db.query(Prediction)
        .filter(Prediction.user_id == user.id)
        .options(joinedload(Prediction.match).joinedload(Match.home_team))
        .options(joinedload(Prediction.match).joinedload(Match.away_team))
        .order_by(Prediction.updated_at.desc())
        .all()
    )
    results = []
    for p in preds:
        pts = None
        if p.match.status == "completed" and p.match.home_score is not None:
            pts = calculate_points(
                p.home_score, p.away_score, p.match.home_score, p.match.away_score
            )["points"]
        results.append(
            MyPredictionOut(
                match_id=p.match_id,
                match_number=p.match.match_number,
                home_team=p.match.home_team.name if p.match.home_team else None,
                away_team=p.match.away_team.name if p.match.away_team else None,
                home_team_code=p.match.home_team.fifa_code if p.match.home_team else None,
                away_team_code=p.match.away_team.fifa_code if p.match.away_team else None,
                home_score=p.home_score,
                away_score=p.away_score,
                points=pts,
                match_status=p.match.status,
            )
        )
    return paginate_list(results, page, page_size)


@router.get("/match/{match_id}", response_model=PaginatedResponse[PredictionOut])
def match_predictions(
    match_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=20),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    preds = (
        db.query(Prediction)
        .filter(Prediction.match_id == match_id)
        .options(joinedload(Prediction.user))
        .order_by(Prediction.updated_at.desc())
        .all()
    )
    results = []
    for p in preds:
        pts = None
        if match.status == "completed" and match.home_score is not None:
            pts = calculate_points(
                p.home_score, p.away_score, match.home_score, match.away_score
            )["points"]
        results.append(
            PredictionOut(
                id=p.id,
                user_id=p.user_id,
                username=p.user.username,
                match_id=p.match_id,
                home_score=p.home_score,
                away_score=p.away_score,
                advance_team_id=p.advance_team_id,
                points=pts,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return paginate_list(results, page, page_size)
