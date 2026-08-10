"""Routes for the viewer's own public profile."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.routes.dependencies import (
    get_current_user_id,
    get_get_my_profile_use_case,
    get_update_my_profile_use_case,
)
from app.schemas.base import SuccessEnvelope
from app.schemas.profile import MyProfileDto, UpdateMyProfileRequest
from app.use_cases.get_my_profile import GetMyProfileUseCase, UserNotFoundError
from app.use_cases.update_my_profile import ProfileValidationError, UpdateMyProfileUseCase

router = APIRouter(tags=["profile"])


@router.get("/me/profile")
async def get_my_profile(
    user_id: Annotated[str, Depends(get_current_user_id)],
    use_case: Annotated[GetMyProfileUseCase, Depends(get_get_my_profile_use_case)],
) -> SuccessEnvelope[MyProfileDto]:
    try:
        profile = await use_case.execute(user_id=user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return SuccessEnvelope(data=profile)


@router.put("/me/profile")
async def update_my_profile(
    payload: UpdateMyProfileRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    use_case: Annotated[UpdateMyProfileUseCase, Depends(get_update_my_profile_use_case)],
) -> SuccessEnvelope[MyProfileDto]:
    try:
        profile = await use_case.execute(user_id=user_id, command=payload)
    except ProfileValidationError:
        raise HTTPException(status_code=422, detail="VALIDATION_ERROR")
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return SuccessEnvelope(data=profile)