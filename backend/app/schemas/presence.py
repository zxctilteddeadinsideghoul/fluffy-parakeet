"""Public DTOs for the Presence context (Request/Response convention)."""

from datetime import datetime

from pydantic import ConfigDict, Field

from app.models.enums import ApproachMode, PresenceStatus, PresenceVisibility
from app.schemas.base import ApiModel


class CheckInRequest(ApiModel):
    """Start a presence session at a venue."""

    venue_token: str = Field(min_length=1)
    visibility: PresenceVisibility
    approach_mode: ApproachMode


class PresenceSessionResponse(ApiModel):
    """Public representation of the viewer's own presence session."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    venue_id: str
    status: PresenceStatus
    visibility: PresenceVisibility
    approach_mode: ApproachMode
    expires_at: datetime


class VenuePresenceCountResponse(ApiModel):
    """Number of currently visible users at a venue."""

    venue_id: str
    count: int = Field(ge=0)