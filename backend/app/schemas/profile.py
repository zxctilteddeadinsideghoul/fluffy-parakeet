"""Public DTOs for the Identity context: my own profile (contract section 5)."""

from datetime import date

from pydantic import Field

from app.models.enums import ApproachMode, CommunicationGoal, MediaModerationStatus
from app.schemas.base import ApiModel


class MyProfilePhotoDto(ApiModel):
    """A photo of the viewer's own profile, including its moderation state."""

    id: str
    url: str
    position: int
    moderationStatus: MediaModerationStatus


class MyProfileDto(ApiModel):
    """The viewer's own public profile (contract section 5)."""

    id: str
    displayName: str
    age: int | None
    birthDate: date | None
    gender: str | None = None
    bio: str | None = None
    communicationGoals: list[CommunicationGoal]
    defaultApproachMode: ApproachMode
    visibilityEnabled: bool
    photos: list[MyProfilePhotoDto] = Field(default_factory=list)
    verification: dict[str, bool]


class UpdateMyProfileRequest(ApiModel):
    """Command UpdateMyProfileCommand (contract section 6)."""

    displayName: str | None = Field(default=None, max_length=100)
    gender: str | None = Field(default=None, max_length=32)
    bio: str | None = Field(default=None, max_length=1000)
    birthDate: date | None = None
    communicationGoals: list[CommunicationGoal] | None = None
    defaultApproachMode: ApproachMode | None = None
    visibilityEnabled: bool | None = None