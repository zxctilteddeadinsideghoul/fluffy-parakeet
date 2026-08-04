"""Public DTOs for the Presence context."""

from pydantic import Field

from app.schemas.base import ApiModel


class VenuePresenceCount(ApiModel):
    """Number of currently visible users at a venue."""

    venue_id: str
    count: int = Field(ge=0)
