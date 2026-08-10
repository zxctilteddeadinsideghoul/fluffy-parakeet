"""Use case: upload a new profile photo."""

from datetime import UTC, datetime
from pathlib import Path

from app.models.enums import MediaModerationStatus
from app.repositories.identity import IdentityRepository
from app.schemas.profile import MyProfileDto
from app.storage.local import InvalidImageTypeError, LocalPhotoStorage
from app.use_cases.get_my_profile import (
    UserNotFoundError,
    build_my_profile_dto,
)


class PhotoUploadError(Exception):
    """Raised when the file is missing, oversized or not an image."""


class UploadProfilePhotoUseCase:
    """Saves the file, appends the photo at the next position (contract §6)."""

    def __init__(
        self,
        repository: IdentityRepository,
        storage: LocalPhotoStorage,
        *,
        media_base_url: str,
        max_upload_bytes: int,
        auto_approve: bool,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._media_base_url = media_base_url.rstrip("/")
        self._max_upload_bytes = max_upload_bytes
        self._auto_approve = auto_approve

    async def execute(self, *, user_id: str, filename: str, content: bytes) -> MyProfileDto:
        user = await self._repository.get_user(user_id)
        if user is None:
            raise UserNotFoundError()
        if not content:
            raise PhotoUploadError("empty file")
        if len(content) > self._max_upload_bytes:
            raise PhotoUploadError("file too large")

        ext = Path(filename).suffix.lower()
        try:
            storage_key = self._storage.save(user_id, ext, content)
        except InvalidImageTypeError:
            raise PhotoUploadError("unsupported image type") from None

        position = (await self._repository.max_photo_position(user_id)) + 1
        photo = await self._repository.add_photo(
            user_id=user_id,
            storage_key=storage_key,
            public_url=None,
            position=position,
            moderation_status=(
                MediaModerationStatus.APPROVED
                if self._auto_approve
                else MediaModerationStatus.PENDING
            ),
        )
        photo.public_url = f"{self._media_base_url}/media/{photo.id}"
        await self._repository.update(photo)
        if self._auto_approve:
            await self._repository.add_photo_verification(
                user_id, datetime.now(UTC).replace(tzinfo=None)
            )

        profile = await self._repository.get_profile(user_id)
        photos = await self._repository.list_photos(user_id)
        is_verified = await self._repository.is_verified_user(
            user_id, datetime.now(UTC).replace(tzinfo=None)
        )
        return build_my_profile_dto(user, profile, photos, is_verified)