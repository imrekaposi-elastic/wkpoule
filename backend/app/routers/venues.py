from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.venue import Venue
from app.routers.auth import get_current_user
from app.schemas.match import VenueDetailOut

router = APIRouter(prefix="/venues", tags=["venues"])


@router.get("", response_model=list[VenueDetailOut])
def list_venues(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Venue).order_by(Venue.name).all()


@router.get("/{venue_id}", response_model=VenueDetailOut)
def get_venue(venue_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue
