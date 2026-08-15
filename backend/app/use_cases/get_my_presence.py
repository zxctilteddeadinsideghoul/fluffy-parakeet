"""Use case: get the viewer's own active presence session."""

from app.repositories.presence import PresenceRepository
from app.schemas.presence import MyPresenceDto


class PresenceNotActiveError(Exception):
    """Raised when the user has no active presence session."""


class GetMyPresenceUseCase:
    """Returns the viewer's own presence session and venue details."""

    def __init__(self, repository: PresenceRepository) -> None:
        self._repository = repository

    async def execute(self, *, user_id: str) -> MyPresenceDto:
        session = await self._repository.find_active_session(user_id)
        if session is None:
            raise PresenceNotActiveError()

        venue = await self._repository.get_venue(session.venue_id)
        venue_name = venue.name if venue is not None else "Unknown Venue"

        return MyPresenceDto(
            status=session.status,
            venue_id=session.venue_id,
            venue_name=venue_name,
            checked_in_at=session.checked_in_at,
            expires_at=session.expires_at,
            visibility=session.visibility,
            approach_mode=session.approach_mode,
        )
