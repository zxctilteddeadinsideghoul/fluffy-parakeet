"""Routes for the viewer's own public profile."""

import asyncio
import mimetypes
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.repositories.identity import IdentityRepository
from app.routes.dependencies import (
    get_current_user_id,
    get_delete_profile_photo_use_case,
    get_get_my_profile_use_case,
    get_photo_storage,
    get_update_my_profile_use_case,
    get_upload_profile_photo_use_case,
)
from app.schemas.base import SuccessEnvelope
from app.schemas.profile import MyProfileDto, UpdateMyProfileRequest
from app.storage.base import PhotoStorage
from app.storage.local import MediaNotFoundError
from app.use_cases.delete_profile_photo import (
    DeleteProfilePhotoUseCase,
    PhotoNotFoundError,
)
from app.use_cases.get_my_profile import GetMyProfileUseCase, UserNotFoundError
from app.use_cases.update_my_profile import ProfileValidationError, UpdateMyProfileUseCase
from app.use_cases.upload_profile_photo import (
    PhotoUploadError,
    UploadProfilePhotoUseCase,
)

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


@router.post("/me/profile/photos")
async def upload_profile_photo(
    file: Annotated[UploadFile, File()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    use_case: Annotated[
        UploadProfilePhotoUseCase, Depends(get_upload_profile_photo_use_case)
    ],
) -> SuccessEnvelope[MyProfileDto]:
    try:
        profile = await use_case.execute(
            user_id=user_id,
            filename=file.filename or "",
            content=await file.read(),
        )
    except PhotoUploadError:
        raise HTTPException(status_code=422, detail="VALIDATION_ERROR") from None
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="NOT_FOUND") from None
    return SuccessEnvelope(data=profile)


@router.delete("/me/profile/photos/{photo_id}")
async def delete_profile_photo(
    photo_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    use_case: Annotated[
        DeleteProfilePhotoUseCase, Depends(get_delete_profile_photo_use_case)
    ],
) -> SuccessEnvelope[MyProfileDto]:
    try:
        profile = await use_case.execute(user_id=user_id, photo_id=photo_id)
    except PhotoNotFoundError:
        raise HTTPException(status_code=404, detail="NOT_FOUND") from None
    return SuccessEnvelope(data=profile)


@router.get("/media/{photo_id}")
async def serve_media_file(
    photo_id: str,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    storage: Annotated[PhotoStorage, Depends(get_photo_storage)],
) -> Response:
    photo = await IdentityRepository(db_session).get_photo(photo_id)
    if photo is None or photo.deleted_at is not None:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    try:
        content = await asyncio.to_thread(storage.open, photo.storage_key)
    except MediaNotFoundError:
        raise HTTPException(status_code=404, detail="NOT_FOUND") from None
    media_type = mimetypes.guess_type(photo.storage_key)[0] or "application/octet-stream"
    return Response(content=content, media_type=media_type)