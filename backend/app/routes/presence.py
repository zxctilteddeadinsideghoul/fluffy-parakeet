"""HTTP routes for the Presence context (thin: only HTTP concerns)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.presence import PresenceSessionOrm
from app.routes.dependencies import (
    get_check_in_use_case,
    get_check_out_use_case,
    get_count_present_users_use_case,
    get_current_user_id,
    get_get_my_presence_use_case,
    get_list_present_profiles_use_case,
    get_present_profile_use_case,
)
from app.schemas.base import SuccessEnvelope
from app.schemas.discovery import PageDto, VisibleProfileDto
from app.schemas.presence import (
    CheckInRequest,
    MyPresenceDto,
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
from app.use_cases.get_my_presence import (
    GetMyPresenceUseCase,
    PresenceNotActiveError as MyPresenceNotActiveError,
)
from app.use_cases.get_present_profile import (
    GetPresentProfileUseCase,
    ProfileNotFoundError,
)
from app.use_cases.list_present_profiles import (
    InvalidCursorError,
    ListPresentProfilesUseCase,
    ViewerNotPresentError,
)
from app.use_cases.list_present_profiles import (
    VenueNotFoundError as ListVenueNotFoundError,
)

router = APIRouter(tags=["presence"])


@router.get("/me/presence", response_model=SuccessEnvelope[MyPresenceDto])
async def get_my_presence(
    use_case: GetMyPresenceUseCase = Depends(get_get_my_presence_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[MyPresenceDto]:
    try:
        presence = await use_case.execute(user_id=user_id)
    except MyPresenceNotActiveError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    return SuccessEnvelope(data=presence)


@router.post(
    "/presence/check-in",
    response_model=SuccessEnvelope[PresenceSessionResponse],
    status_code=201,
)
async def check_in(
    payload: CheckInRequest,
    use_case: CheckInUseCase = Depends(get_check_in_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[PresenceSessionResponse]:
    try:
        session: PresenceSessionOrm = await use_case.execute(user_id=user_id, command=payload)
    except (UserNotActiveError, VerificationRequiredError):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "FORBIDDEN") from None
    except (InvalidCheckInTokenError, CheckInVenueNotFoundError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    except PresenceAlreadyActiveError:
        raise HTTPException(status.HTTP_409_CONFLICT, "INVALID_STATE_TRANSITION") from None
    return SuccessEnvelope(data=PresenceSessionResponse.model_validate(session))


@router.post("/presence/check-out", response_model=SuccessEnvelope[PresenceSessionResponse])
async def check_out(
    use_case: CheckOutUseCase = Depends(get_check_out_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[PresenceSessionResponse]:
    try:
        session = await use_case.execute(user_id=user_id)
    except PresenceNotActiveError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    return SuccessEnvelope(data=PresenceSessionResponse.model_validate(session))


@router.get(
    "/venues/{venue_id}/presence/count",
    response_model=SuccessEnvelope[VenuePresenceCountResponse],
)
async def get_venue_presence_count(
    venue_id: str,
    use_case: CountPresentUsersUseCase = Depends(get_count_present_users_use_case),
) -> SuccessEnvelope[VenuePresenceCountResponse]:
    try:
        count = await use_case.execute(venue_id=venue_id)
    except CountVenueNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    return SuccessEnvelope(data=VenuePresenceCountResponse(venue_id=venue_id, count=count))


@router.get("/venues/{venue_id}/profiles", response_model=SuccessEnvelope[PageDto])
async def list_present_profiles(
    venue_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    use_case: ListPresentProfilesUseCase = Depends(get_list_present_profiles_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[PageDto]:
    try:
        items, next_cursor = await use_case.execute(
            venue_id=venue_id,
            viewer_user_id=user_id,
            limit=limit,
            cursor=cursor,
        )
    except ViewerNotPresentError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "ACTIVE_PRESENCE_REQUIRED"
        ) from None
    except InvalidCursorError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "INVALID_CURSOR"
        ) from None
    except ListVenueNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    return SuccessEnvelope(data=PageDto(items=items, nextCursor=next_cursor))


@router.get(
    "/presence/{presence_id}/profile",
    response_model=SuccessEnvelope[VisibleProfileDto],
)
async def get_present_user_profile(
    presence_id: str,
    use_case: GetPresentProfileUseCase = Depends(get_present_profile_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[VisibleProfileDto]:
    try:
        return SuccessEnvelope(
            data=await use_case.execute(presence_id=presence_id, viewer_user_id=user_id)
        )
    except ProfileNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    except ViewerNotPresentError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "ACTIVE_PRESENCE_REQUIRED"
        ) from None