"""HTTP routes for the Presence context."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.repositories.presence import PresenceRepository
from app.schemas.presence import VenuePresenceCount
from app.services.presence import CountPresentUsersUseCase, VenueNotFoundError

router = APIRouter(prefix="/venues/{venue_id}/presence", tags=["presence"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/count", response_model=VenuePresenceCount)
def get_venue_presence_count(venue_id: str, db: Session = Depends(get_db)) -> VenuePresenceCount:
    use_case = CountPresentUsersUseCase(PresenceRepository(db))
    try:
        count = use_case.execute(venue_id)
    except VenueNotFoundError:
        raise HTTPException(status_code=404, detail="NOT_FOUND") from None
    return VenuePresenceCount(venue_id=venue_id, count=count)
