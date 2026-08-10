"""Public DTOs for the Discovery context (swipe deck of present users)."""

from typing import Literal

from pydantic import ConfigDict, Field

from app.models.enums import ApproachMode, CommunicationGoal
from app.schemas.base import ApiModel

AvailableAction = Literal["contact", "drink", "ask_to_approach"]


class ProfilePhotoDto(ApiModel):
    """A single approved profile photo, safe to display."""

    id: str
    url: str
    position: int


class VisibleProfileDto(ApiModel):
    """Safe public representation of another present user (contract section 5)."""

    model_config = ConfigDict(from_attributes=True)

    userId: str
    presenceId: str
    venueId: str
    displayName: str
    age: int
    gender: str | None = None
    bio: str | None = None
    communicationGoals: list[CommunicationGoal]
    approachMode: ApproachMode
    photos: list[ProfilePhotoDto] = Field(default_factory=list)
    isVerified: bool
    availableActions: list[AvailableAction] = Field(default_factory=list)


class PageDto(ApiModel):
    """Cursor-based page, aligned with docs/CONTRACTS_DATA.md section 2."""

    items: list[VisibleProfileDto]
    nextCursor: str | None = None
