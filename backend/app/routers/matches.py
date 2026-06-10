from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth import get_admin_user, get_current_user
from app.cache.helpers import cached_call_async
from app.cache.invalidation import invalidate_on_score_update
from app.cache.keys import CacheKeys
from app.cache.ttl import MATCHES_TTL
from app.database import get_db
from app.models.match import Match
from app.models.user import User
from app.schemas.match import (
    CalendarMetaOut,
    ExpertPrediction,
    FunCommentOut,
    MatchOut,
    ScoreUpdate,
    VenueOut,
    TeamOut,
)
from app.schemas.pagination import DEFAULT_PAGE_SIZE, PaginatedResponse, paginate_list
from app.services.bracket_resolver import compute_predicted_knockout_teams
from app.services.expert import generate_expert_prediction
from app.services.match_calendar import local_date_for_utc_instant, utc_bounds_for_local_day
from app.services.next_match_prediction import first_match_needing_prediction
from app.services.prediction_lock import match_accepts_prediction_updates
from app.services.scoring import recalculate_points
from app.services.team_names import team_matches_search, team_out_matches_search
from app.services.weather import get_match_temperature

router = APIRouter()


def _match_matches_search(
    m: Match,
    term: str,
    predicted_pair: tuple[TeamOut | None, TeamOut | None] | None = None,
) -> bool:
    needle = term.strip()
    if not needle:
        return True
    if team_matches_search(m.home_team, needle) or team_matches_search(m.away_team, needle):
        return True
    if predicted_pair:
        for team in predicted_pair:
            if team and team_out_matches_search(team.fifa_code, team.name, needle):
                return True
    venue = m.venue
    if venue is None:
        return False
    normalized = needle.casefold()
    return normalized in venue.name.casefold() or normalized in venue.city.casefold()


def _match_to_out(
    m: Match,
    temperature: float | None = None,
    predicted_pair: tuple[TeamOut | None, TeamOut | None] | None = None,
    bracket_slots: tuple[str | None, str | None] | None = None,
) -> MatchOut:
    home_team = TeamOut.model_validate(m.home_team) if m.home_team else None
    away_team = TeamOut.model_validate(m.away_team) if m.away_team else None
    if home_team is None and predicted_pair and predicted_pair[0]:
        home_team = predicted_pair[0]
    if away_team is None and predicted_pair and predicted_pair[1]:
        away_team = predicted_pair[1]

    expert: ExpertPrediction | None = None
    if home_team and away_team:
        expert = generate_expert_prediction(
            home_team.world_ranking,
            away_team.world_ranking,
            home_team.fifa_code,
            away_team.fifa_code,
        )

    bh, ba = bracket_slots if bracket_slots else (None, None)

    return MatchOut(
        id=m.id,
        match_number=m.match_number,
        stage=m.stage,
        group_letter=m.group_letter,
        home_team=home_team,
        away_team=away_team,
        bracket_home_slot=bh,
        bracket_away_slot=ba,
        venue=VenueOut.model_validate(m.venue),
        kickoff_utc=m.kickoff_utc,
        home_score=m.home_score,
        away_score=m.away_score,
        status=m.status,
        fun_comment=FunCommentOut.model_validate(m.fun_comment) if m.fun_comment else None,
        temperature_celsius=temperature,
        expert_prediction=expert,
        prediction_editable=match_accepts_prediction_updates(m),
    )


@router.get("", response_model=PaginatedResponse[MatchOut])
async def list_matches(
    stage: str | None = None,
    group: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=20),
    predicted_teams: bool = Query(False, description="Fill knockout TBD teams from your predictions"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cache_key = CacheKeys.matches_list(
        stage, group, search, page, page_size, predicted_teams, user.id
    )

    async def compute() -> PaginatedResponse[MatchOut]:
        q = db.query(Match).options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
            joinedload(Match.fun_comment),
        )
        if stage:
            q = q.filter(Match.stage == stage)
        if group:
            q = q.filter(Match.group_letter == group)

        ordered = q.order_by(Match.kickoff_utc).all()

        predicted_map: dict[int, tuple[TeamOut | None, TeamOut | None]] = {}
        bracket_map: dict[int, tuple[str | None, str | None]] = {}
        if predicted_teams or (search and search.strip()):
            predicted_map, bracket_map = compute_predicted_knockout_teams(db, user.id)

        if search and search.strip():
            ordered = [
                m
                for m in ordered
                if _match_matches_search(m, search, predicted_map.get(m.match_number))
            ]

        paged = paginate_list(ordered, page, page_size)

        if predicted_teams and not predicted_map:
            predicted_map, bracket_map = compute_predicted_knockout_teams(db, user.id)

        results = []
        for m in paged.items:
            temp = await get_match_temperature(m.id, m.venue.city, m.kickoff_utc)
            pair = predicted_map.get(m.match_number)
            slots = bracket_map.get(m.match_number)
            results.append(_match_to_out(m, temp, pair, slots))
        return PaginatedResponse(
            items=results,
            total=paged.total,
            page=paged.page,
            page_size=paged.page_size,
            total_pages=paged.total_pages,
        )

    return await cached_call_async(
        cache_key, MATCHES_TTL, PaginatedResponse[MatchOut], compute
    )


@router.get("/calendar-meta", response_model=CalendarMetaOut)
def calendar_meta(
    tz: str = Query(..., min_length=1, max_length=64, description="IANA timezone"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    first_kickoff = db.query(func.min(Match.kickoff_utc)).scalar()
    if first_kickoff is None:
        raise HTTPException(status_code=404, detail="No matches scheduled")
    try:
        first_local = local_date_for_utc_instant(first_kickoff, tz)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CalendarMetaOut(
        first_kickoff_utc=first_kickoff,
        first_match_local_date=first_local,
    )


@router.get("/next-needing-prediction", response_model=MatchOut | None)
async def next_match_needing_prediction(
    predicted_teams: bool = Query(True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = first_match_needing_prediction(db, user.id)
    if m is None:
        return None
    temp = await get_match_temperature(m.id, m.venue.city, m.kickoff_utc)
    pair = None
    slots = None
    if predicted_teams and m.match_number >= 73:
        pmap, smap = compute_predicted_knockout_teams(db, user.id)
        pair = pmap.get(m.match_number)
        slots = smap.get(m.match_number)
    return _match_to_out(m, temp, pair, slots)


@router.get("/by-number/{match_number}", response_model=MatchOut)
async def get_match_by_match_number(
    match_number: int,
    predicted_teams: bool = Query(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resolve a fixture by FIFA schedule match number (1–104), not database primary key."""
    m = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
            joinedload(Match.fun_comment),
        )
        .filter(Match.match_number == match_number)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    temp = await get_match_temperature(m.id, m.venue.city, m.kickoff_utc)
    pair = None
    slots = None
    if predicted_teams and m.match_number >= 73:
        pmap, smap = compute_predicted_knockout_teams(db, user.id)
        pair = pmap.get(m.match_number)
        slots = smap.get(m.match_number)
    return _match_to_out(m, temp, pair, slots)


@router.get("/by-day", response_model=list[MatchOut])
async def matches_by_day(
    date: date = Query(..., description="Local calendar date (YYYY-MM-DD)"),
    tz: str = Query(..., min_length=1, max_length=64, description="IANA timezone"),
    predicted_teams: bool = Query(True, description="Fill knockout TBD teams from your predictions"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        start_utc, end_utc = utc_bounds_for_local_day(date, tz)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    rows = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
            joinedload(Match.fun_comment),
        )
        .filter(Match.kickoff_utc >= start_utc, Match.kickoff_utc <= end_utc)
        .order_by(Match.kickoff_utc)
        .all()
    )

    predicted_map: dict[int, tuple[TeamOut | None, TeamOut | None]] = {}
    bracket_map: dict[int, tuple[str | None, str | None]] = {}
    if predicted_teams:
        predicted_map, bracket_map = compute_predicted_knockout_teams(db, user.id)

    return [
        _match_to_out(
            m,
            None,
            predicted_map.get(m.match_number),
            bracket_map.get(m.match_number),
        )
        for m in rows
    ]


@router.get("/{match_id}", response_model=MatchOut)
async def get_match(
    match_id: int,
    predicted_teams: bool = Query(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cache_key = CacheKeys.match_detail(match_id, predicted_teams, user.id)

    async def compute() -> MatchOut:
        m = (
            db.query(Match)
            .options(
                joinedload(Match.home_team),
                joinedload(Match.away_team),
                joinedload(Match.venue),
                joinedload(Match.fun_comment),
            )
            .filter(Match.id == match_id)
            .first()
        )
        if not m:
            raise HTTPException(status_code=404, detail="Match not found")
        temp = await get_match_temperature(m.id, m.venue.city, m.kickoff_utc)
        pair = None
        slots = None
        if predicted_teams and m.match_number >= 73:
            pmap, smap = compute_predicted_knockout_teams(db, user.id)
            pair = pmap.get(m.match_number)
            slots = smap.get(m.match_number)
        return _match_to_out(m, temp, pair, slots)

    return await cached_call_async(cache_key, MATCHES_TTL, MatchOut, compute)


@router.patch("/{match_id}/score", response_model=MatchOut)
async def update_score(
    match_id: int,
    body: ScoreUpdate,
    _admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    m = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
            joinedload(Match.fun_comment),
        )
        .filter(Match.id == match_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    m.home_score = body.home_score
    m.away_score = body.away_score
    m.status = body.status
    db.commit()
    db.refresh(m)
    recalculate_points()
    await invalidate_on_score_update()
    temp = await get_match_temperature(m.id, m.venue.city, m.kickoff_utc)
    return _match_to_out(m, temp)
