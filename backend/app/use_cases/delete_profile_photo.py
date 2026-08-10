"""Use case: soft-delete one of the caller's own profile photos."""

from datetime import UTC, datetime

from app.repositories.identity import IdentityRepository
from app.schemas.profile import MyProfileDto
from app.use_cases.get_my_profile import (
    UserNotFoundError,
    build_my_profile_dto,
)


class PhotoNotFoundError(Exception):
    """Raised when the photo is missing, deleted, or owned by someone else."""


class DeleteProfilePhotoUseCase:
    """Soft-deletes the photo (deletedAt); never reveals other users' photos."""

    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    async def execute(self, *, user_id: str, photo_id: str) -> MyProfileDto:
        photo = await self._repository.get_photo(photo_id)
        if photo is None or photo.user_id != user_id or photo.deleted_at is not None:
            raise PhotoNotFoundError()
        photo.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        await self._repository.update(photo)

        user = await self._repository.get_user(user_id)
        if user is None:
            raise UserNotFoundError()
        profile = await self._repository.get_profile(user_id)
        photos = await self._repository.list_photos(user_id)
        is_verified = await self._repository.is_verified_user(
            user_id, datetime.now(UTC).replace(tzinfo=None)
        )
        return build_my_profile_dto(user, profile, photos, is_verified)