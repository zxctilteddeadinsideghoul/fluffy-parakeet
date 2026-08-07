"""HTTP routes for the Presence context (thin: only HTTP concerns)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.presence import PresenceSessionOrm
from app.routes.dependencies import (
    get_check_in_use_case,
    get_check_out_use_case,
    get_count_present_users_use_case,
    get_current_user_id,
)
from app.schemas.presence import (
    CheckInRequest,
    PresenceSessionResponse,
    VenuePresenceCountResponse,
)
from app.use_cases.check_in import (
    CheckInUseCase,
    InvalidCheckInTokenError,
    PresenceAlreadyActiveError,
    UserNotActiveError,
    VerificationRequiredError,
)
from app.use_cases.check_in import (
    VenueNotFoundError as CheckInVenueNotFoundError,
)
from app.use_cases.check_out import CheckOutUseCase, PresenceNotActiveError
from app.use_cases.count_present_users import (
    CountPresentUsersUseCase,
)
from app.use_cases.count_present_users import (
    VenueNotFoundError as CountVenueNotFoundError,
)

router = APIRouter(tags=["presence"])


@router.post("/presence/check-in", response_model=PresenceSessionResponse, status_code=201)
async def check_in(
    payload: CheckInRequest,
    use_case: CheckInUseCase = Depends(get_check_in_use_case),
    user_id: str = Depends(get_current_user_id),
) -> PresenceSessionResponse:
    try:
        session: PresenceSessionOrm = await use_case.execute(user_id=user_id, command=payload)
    except (UserNotActiveError, VerificationRequiredError):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "FORBIDDEN") from None
    except (InvalidCheckInTokenError, CheckInVenueNotFoundError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    except PresenceAlreadyActiveError:
        raise HTTPException(status.HTTP_409_CONFLICT, "INVALID_STATE_TRANSITION") from None
    return PresenceSessionResponse.model_validate(session)


@router.post("/presence/check-out", response_model=PresenceSessionResponse)
async def check_out(
    use_case: CheckOutUseCase = Depends(get_check_out_use_case),
    user_id: str = Depends(get_current_user_id),
) -> PresenceSessionResponse:
    try:
        session = await use_case.execute(user_id=user_id)
    except PresenceNotActiveError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    return PresenceSessionResponse.model_validate(session)


@router.get("/venues/{venue_id}/presence/count", response_model=VenuePresenceCountResponse)
async def get_venue_presence_count(
    venue_id: str,
    use_case: CountPresentUsersUseCase = Depends(get_count_present_users_use_case),
) -> VenuePresenceCountResponse:
    try:
        count = await use_case.execute(venue_id=venue_id)
    except CountVenueNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    return VenuePresenceCountResponse(venue_id=venue_id, count=count)