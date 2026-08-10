"""Use case: show the viewer's own public profile."""

from datetime import UTC, datetime

from app.models.enums import ApproachMode, CommunicationGoal
from app.models.user import ProfileOrm, UserOrm
from app.repositories.identity import IdentityRepository
from app.schemas.profile import MyProfileDto, MyProfilePhotoDto
from app.use_cases.list_present_profiles import age


class UserNotFoundError(Exception):
    """Raised when the account does not exist."""


def build_my_profile_dto(
    user: UserOrm,
    profile: ProfileOrm | None,
    photos: list,
    is_verified: bool,
) -> MyProfileDto:
    if profile is None:
        return MyProfileDto(
            id=user.id,
            displayName="",
            age=age(user.birth_date),
            defaultApproachMode=ApproachMode.ASK_BEFORE_APPROACH,
            verification={"isVerified": is_verified},
        )

    goals = [
        CommunicationGoal(part)
        for part in profile.communication_goals.split(",")
        if part
    ]
    return MyProfileDto(
        id=user.id,
        displayName=profile.display_name,
        age=age(user.birth_date),
        gender=profile.gender,
        bio=profile.bio,
        communicationGoals=goals,
        defaultApproachMode=profile.default_approach_mode,
        photos=[
            MyProfilePhotoDto(
                id=photo.id,
                url=photo.public_url or "",
                position=photo.position,
                moderationStatus=photo.moderation_status,
            )
            for photo in photos
        ],
        verification={"isVerified": is_verified},
    )


class GetMyProfileUseCase:
    """Returns the viewer's own profile; never another user's data."""

    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    async def execute(self, *, user_id: str) -> MyProfileDto:
        user = await self._repository.get_user(user_id)
        if user is None:
            raise UserNotFoundError()
        profile = await self._repository.get_profile(user_id)
        photos = await self._repository.list_photos(user_id)
        is_verified = await self._repository.is_verified_user(
            user_id, datetime.now(UTC).replace(tzinfo=None)
        )
        return build_my_profile_dto(user, profile, photos, is_verified)