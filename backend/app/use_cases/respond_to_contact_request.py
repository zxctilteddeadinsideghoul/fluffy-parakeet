"""Use case: accept or decline a contact request (contract 4.3).

Accepting atomically creates one Connection, one Conversation and two
ConversationMembers; declining just marks the request.
"""

import logging
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import (
    ConnectionOrm,
    ContactRequestOrm,
    ConversationMemberOrm,
    ConversationOrm,
)
from app.models.enums import RequestStatus
from app.repositories.communication import CommunicationRepository
from app.services.events import EventPublisher, event_publisher

logger = logging.getLogger(__name__)

RespondDecision = Literal["accept", "decline"]


class RequestNotFoundError(Exception):
    """Raised when the request does not exist or belongs to another user."""


class RequestExpiredError(Exception):
    """Raised when the request is past its expiration."""


class InvalidStateTransitionError(Exception):
    """Raised when the request is not pending anymore."""


class RespondToContactRequestUseCase:
    def __init__(
        self,
        session: AsyncSession,
        repository: CommunicationRepository,
        publisher: EventPublisher = event_publisher,
    ) -> None:
        self._session = session
        self._repository = repository
        self._publisher = publisher

    async def execute(
        self, *, user_id: str, request_id: str, decision: RespondDecision
    ) -> ContactRequestOrm:
        now = datetime.now(UTC).replace(tzinfo=None)
        request = await self._repository.get_request(request_id)
        if request is None or request.recipient_user_id != user_id:
            raise RequestNotFoundError()
        if request.status != RequestStatus.PENDING:
            raise InvalidStateTransitionError()
        if request.expires_at <= now:
            request.status = RequestStatus.EXPIRED
            await self._session.flush()
            await self._publisher.publish("contact_request.expired.v1", request.id, user_id)
            await self._session.commit()
            raise RequestExpiredError()

        request.responded_at = now
        if decision == "decline":
            request.status = RequestStatus.DECLINED
            await self._session.flush()
            await self._publisher.publish("contact_request.declined.v1", request.id, user_id)
            await self._session.commit()
            return request

        connection = await self._repository.add_connection(
            ConnectionOrm(
                user_a_id=request.sender_user_id,
                user_b_id=request.recipient_user_id,
                venue_id=request.venue_id,
                source_request_id=request.id,
            )
        )
        conversation = await self._repository.add_conversation(
            ConversationOrm(connection_id=connection.id)
        )
        await self._repository.add_member(
            ConversationMemberOrm(conversation_id=conversation.id, user_id=request.sender_user_id)
        )
        await self._repository.add_member(
            ConversationMemberOrm(conversation_id=conversation.id, user_id=request.recipient_user_id)
        )
        request.status = RequestStatus.ACCEPTED
        await self._session.flush()
        await self._publisher.publish("contact_request.accepted.v1", request.id, user_id)
        await self._publisher.publish("connection.created.v1", connection.id, user_id)
        await self._session.commit()
        return request
