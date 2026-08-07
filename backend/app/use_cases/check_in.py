"""Use case: check in (start presence at a venue)."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import CheckInMethod, PresenceStatus, UserStatus, VenueStatus
from app.models.presence import PresenceSessionOrm
from app.repositories.presence import PresenceRepository
from app.schemas.presence import CheckInRequest
from app.services.events import EventPublisher, event_publisher


class UserNotActiveError(Exception):
    """Raised when the user account is not active."""


class VerificationRequiredError(Exception):
    """Raised when the user has no valid verification."""


class InvalidCheckInTokenError(Exception):
    """Raised when the check-in token is missing, revoked or expired."""


class VenueNotFoundError(Exception):
    """Raised when the venue does not exist or is not active."""


class PresenceAlreadyActiveError(Exception):
    """Raised when the user already has an active or hidden session."""


class CheckInUseCase:
    """Starts a presence session for the user at the venue behind the token."""

    def __init__(
        self,
        session: AsyncSession,
        repository: PresenceRepository,
        ttl_hours: int = settings.presence_ttl_hours,
        publisher: EventPublisher = event_publisher,
    ) -> None:
        self._session = session
        self._repository = repository
        self._ttl_hours = ttl_hours
        self._publisher = publisher

    async def execute(self, *, user_id: str, command: CheckInRequest) -> PresenceSessionOrm:
        if await self._repository.user_status(user_id) != UserStatus.ACTIVE:
            raise UserNotActiveError(user_id)
        if not await self._repository.is_verified_user(
            user_id, datetime.now(UTC).replace(tzinfo=None)
        ):
            raise VerificationRequiredError(user_id)

        now = datetime.now(UTC).replace(tzinfo=None)
        token_hash = sha256(command.venue_token.encode()).hexdigest()
        token = await self._repository.find_active_token(token_hash, now)
        if token is None:
            raise InvalidCheckInTokenError()
        if await self._repository.venue_status(token.venue_id) != VenueStatus.ACTIVE.value:
            raise VenueNotFoundError(token.venue_id)
        if await self._repository.find_active_session(user_id) is not None:
            raise PresenceAlreadyActiveError(user_id)

        session = await self._repository.add_session(
            PresenceSessionOrm(
                user_id=user_id,
                venue_id=token.venue_id,
                status=PresenceStatus.ACTIVE,
                visibility=command.visibility,
                approach_mode=command.approach_mode,
                check_in_method=CheckInMethod.VENUE_QR,
                checked_in_at=now,
                last_heartbeat_at=now,
                expires_at=now + timedelta(hours=self._ttl_hours),
            )
        )
        await self._publisher.publish("presence.started.v1", session.id, user_id)
        await self._session.commit()
        return session