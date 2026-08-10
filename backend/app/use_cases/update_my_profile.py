"""Use case: update the viewer's own public profile."""

from datetime import UTC, datetime

from app.models.user import ProfileOrm
from app.repositories.identity import IdentityRepository
from app.schemas.profile import MyProfileDto, UpdateMyProfileRequest
from app.use_cases.get_my_profile import (
    UserNotFoundError,
    build_my_profile_dto,
)


class ProfileValidationError(Exception):
    """Raised when the incoming command violates profile rules."""


class UpdateMyProfileUseCase:
    """Applies UpdateMyProfileCommand to the caller's own profile only."""

    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    async def execute(
        self, *, user_id: str, command: UpdateMyProfileRequest
    ) -> MyProfileDto:
        user = await self._repository.get_user(user_id)
        if user is None:
            raise UserNotFoundError()

        profile = await self._repository.get_profile(user_id)
        if profile is None:
            profile = ProfileOrm(user_id=user_id)

        if command.visibilityEnabled and not command.displayName.strip():
            raise ProfileValidationError(
                "displayName is required when visibility is enabled"
            )

        profile.display_name = command.displayName.strip()
        profile.gender = command.gender
        profile.bio = command.bio
        profile.communication_goals = ",".join(
            goal.value for goal in command.communicationGoals
        )
        profile.default_approach_mode = command.defaultApproachMode
        profile.visibility_enabled = command.visibilityEnabled
        user.birth_date = command.birthDate

        await self._repository.update(profile)
        await self._repository.update(user)

        photos = await self._repository.list_photos(user_id)
        is_verified = await self._repository.is_verified_user(
            user_id, datetime.now(UTC).replace(tzinfo=None)
        )
        return build_my_profile_dto(user, profile, photos, is_verified)