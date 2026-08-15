"""Use case: send a contact request to a present user (contract 4.3)."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.communication import ContactRequestOrm
from app.models.enums import PresenceStatus, RequestStatus, UserStatus
from app.repositories.communication import CommunicationRepository
from app.schemas.communication import SendContactRequestRequest
from app.services.events import EventPublisher, event_publisher

logger = logging.getLogger(__name__)


class UserNotActiveError(Exception):
    """Raised when the sender account is not active."""


class VerificationRequiredError(Exception):
    """Raised when the sender has no valid verification."""


class NoActivePresenceError(Exception):
    """Raised when the sender has no active presence session."""


class RecipientNotPresentError(Exception):
    """Raised when the recipient presence does not exist."""


class NotSameVenueError(Exception):
    """Raised when the recipient presence is not active at the sender's venue."""


class SelfInteractionError(Exception):
    """Raised when the sender tries to contact themselves."""


class BlockedError(Exception):
    """Raised when either side has blocked the other."""


class RequestAlreadyExistsError(Exception):
    """Raised when a duplicate request within the same visit is sent."""


class SendContactRequestUseCase:
    """Creates a pending contact request between two present users."""

    def __init__(
        self,
        session: AsyncSession,
        repository: CommunicationRepository,
        ttl_minutes: int = settings.contact_request_ttl_minutes,
        publisher: EventPublisher = event_publisher,
    ) -> None:
        self._session = session
        self._repository = repository
        self._ttl_minutes = ttl_minutes
        self._publisher = publisher

    async def execute(
        self, *, user_id: str, command: SendContactRequestRequest
    ) -> ContactRequestOrm:
        now = datetime.now(UTC).replace(tzinfo=None)
        sender_session = await self._repository.find_active_session(user_id, now)
        if sender_session is None:
            raise NoActivePresenceError()
        if await self._repository.user_status(user_id) != UserStatus.ACTIVE:
            raise UserNotActiveError(user_id)
        if not await self._repository.is_verified_user(user_id, now):
            raise VerificationRequiredError(user_id)

        recipient_session = await self._repository.get_session(command.recipient_presence_id)
        if recipient_session is None:
            raise RecipientNotPresentError()
        if (
            recipient_session.status != PresenceStatus.ACTIVE
            or recipient_session.expires_at <= now
            or recipient_session.venue_id != sender_session.venue_id
        ):
            raise NotSameVenueError()
        recipient_user_id = recipient_session.user_id
        if recipient_user_id == user_id:
            raise SelfInteractionError()
        if await self._repository.has_block_between(user_id, recipient_user_id):
            raise BlockedError()
        if (
            await self._repository.find_duplicate_request(
                user_id, recipient_user_id, recipient_session.id
            )
            is not None
        ):
            raise RequestAlreadyExistsError()

        logger.info(
            "send contact request: sender=%s recipient=%s venue=%s",
            user_id,
            recipient_user_id,
            sender_session.venue_id,
        )
        request = await self._repository.add_request(
            ContactRequestOrm(
                sender_user_id=user_id,
                recipient_user_id=recipient_user_id,
                sender_presence_id=sender_session.id,
                recipient_presence_id=recipient_session.id,
                venue_id=sender_session.venue_id,
                status=RequestStatus.PENDING,
                message=command.message,
                expires_at=now + timedelta(minutes=self._ttl_minutes),
            )
        )
        await self._publisher.publish("contact_request.created.v1", request.id, user_id)
        await self._session.commit()
        return request
