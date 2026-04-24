from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.match import Match
from app.models.venue import Venue
from app.routers.auth import get_current_user
from app.schemas.match import VenueDetailOut, VenueScheduledMatchOut
from app.services.match_attractiveness import compute_attractiveness_stars

router = APIRouter(prefix="/venues", tags=["venues"])


def _scheduled_match_row(m: Match) -> VenueScheduledMatchOut:
    stars = compute_attractiveness_stars(m)
    hn = m.home_team.name if m.home_team else None
    an = m.away_team.name if m.away_team else None
    hc = m.home_team.fifa_code if m.home_team else None
    ac = m.away_team.fifa_code if m.away_team else None
    return VenueScheduledMatchOut(
        match_id=m.id,
        match_number=m.match_number,
        stage=m.stage,
        group_letter=m.group_letter,
        kickoff_utc=m.kickoff_utc,
        home_team_name=hn,
        away_team_name=an,
        home_team_code=hc,
        away_team_code=ac,
        attractiveness_stars=stars,
    )


def _load_matches_by_venue(db: Session, venue_ids: list[int]) -> dict[int, list[VenueScheduledMatchOut]]:
    if not venue_ids:
        return {}
    rows = (
        db.query(Match)
        .filter(Match.venue_id.in_(venue_ids))
        .options(joinedload(Match.home_team), joinedload(Match.away_team))
        .order_by(Match.kickoff_utc)
        .all()
    )
    by_vid: dict[int, list[VenueScheduledMatchOut]] = defaultdict(list)
    for m in rows:
        by_vid[m.venue_id].append(_scheduled_match_row(m))
    return dict(by_vid)


def _venue_detail_out(venue: Venue, matches: list[VenueScheduledMatchOut]) -> VenueDetailOut:
    base = VenueDetailOut.model_validate(venue)
    return base.model_copy(update={"matches": matches})


@router.get("", response_model=list[VenueDetailOut])
def list_venues(db: Session = Depends(get_db), _=Depends(get_current_user)):
    venues = db.query(Venue).order_by(Venue.name).all()
    by_vid = _load_matches_by_venue(db, [v.id for v in venues])
    return [_venue_detail_out(v, by_vid.get(v.id, [])) for v in venues]


@router.get("/{venue_id}", response_model=VenueDetailOut)
def get_venue(venue_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    by_vid = _load_matches_by_venue(db, [venue_id])
    return _venue_detail_out(venue, by_vid.get(venue_id, []))
