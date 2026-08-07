"""Use case: check out (end the current presence session)."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.presence import PresenceSessionOrm
from app.repositories.presence import PresenceRepository
from app.services.events import EventPublisher, event_publisher


class PresenceNotActiveError(Exception):
    """Raised when the user has no active or hidden session to end."""


class CheckOutUseCase:
    """Ends the user's current presence session."""

    def __init__(
        self,
        session: AsyncSession,
        repository: PresenceRepository,
        publisher: EventPublisher = event_publisher,
    ) -> None:
        self._session = session
        self._repository = repository
        self._publisher = publisher

    async def execute(self, *, user_id: str) -> PresenceSessionOrm:
        session = await self._repository.find_active_session(user_id)
        if session is None:
            raise PresenceNotActiveError(user_id)
        session = await self._repository.end_session(
            session, datetime.now(UTC).replace(tzinfo=None)
        )
        await self._publisher.publish("presence.ended.v1", session.id, user_id)
        await self._session.commit()
        return session