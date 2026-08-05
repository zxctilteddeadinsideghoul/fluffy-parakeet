"""HTTP routes for the Presence context."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.presence import PresenceRepository
from app.schemas.presence import CheckInCommand, PresenceSessionDto, VenuePresenceCount
from app.services.presence import (
    CheckInUseCase,
    CheckOutUseCase,
    CountPresentUsersUseCase,
    InvalidCheckInTokenError,
    PresenceAlreadyActiveError,
    PresenceNotActiveError,
    UserNotActiveError,
    VenueNotFoundError,
    VerificationRequiredError,
)

router = APIRouter(tags=["presence"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[str, Depends(get_current_user_id)]


@router.post("/presence/check-in", response_model=PresenceSessionDto, status_code=201)
def check_in(command: CheckInCommand, db: DbSession, user_id: CurrentUser) -> PresenceSessionDto:
    use_case = CheckInUseCase(PresenceRepository(db), settings.presence_ttl_hours)
    try:
        return use_case.execute(user_id, command)
    except (UserNotActiveError, VerificationRequiredError):
        raise HTTPException(status_code=403, detail="FORBIDDEN") from None
    except (InvalidCheckInTokenError, VenueNotFoundError):
        raise HTTPException(status_code=404, detail="NOT_FOUND") from None
    except PresenceAlreadyActiveError:
        raise HTTPException(status_code=409, detail="INVALID_STATE_TRANSITION") from None


@router.post("/presence/check-out", response_model=PresenceSessionDto)
def check_out(db: DbSession, user_id: CurrentUser) -> PresenceSessionDto:
    use_case = CheckOutUseCase(PresenceRepository(db))
    try:
        return use_case.execute(user_id)
    except PresenceNotActiveError:
        raise HTTPException(status_code=404, detail="NOT_FOUND") from None


@router.get("/venues/{venue_id}/presence/count", response_model=VenuePresenceCount)
def get_venue_presence_count(venue_id: str, db: DbSession) -> VenuePresenceCount:
    use_case = CountPresentUsersUseCase(PresenceRepository(db))
    try:
        count = use_case.execute(venue_id)
    except VenueNotFoundError:
        raise HTTPException(status_code=404, detail="NOT_FOUND") from None
    return VenuePresenceCount(venue_id=venue_id, count=count)
