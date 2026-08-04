"""Use case: how many people are currently present at a venue."""

from datetime import datetime, timezone

from app.repositories.presence import PresenceRepository


class VenueNotFoundError(Exception):
    """Raised when the venue does not exist."""


class CountPresentUsersUseCase:
    """Counts users currently visible to the viewer at a venue."""

    def __init__(self, repository: PresenceRepository):
        self.repository = repository

    def execute(self, venue_id: str, viewer_user_id: str | None = None) -> int:
        if not self.repository.venue_exists(venue_id):
            raise VenueNotFoundError(venue_id)
        now = datetime.now(timezone.utc)
        return self.repository.count_visible_users(venue_id, viewer_user_id, now)
