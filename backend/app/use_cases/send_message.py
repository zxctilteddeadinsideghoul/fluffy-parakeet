"""Use case: send a message in a conversation (contract 4.3)."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import MessageOrm
from app.models.enums import ConversationStatus
from app.repositories.communication import CommunicationRepository
from app.schemas.communication import SendMessageRequest
from app.services.events import EventPublisher, event_publisher

logger = logging.getLogger(__name__)


class ConversationNotFoundError(Exception):
    """Raised when the conversation does not exist or is hidden from the user."""


class NotMemberError(Exception):
    """Raised when the sender is not an active member of the conversation."""


class InvalidStateTransitionError(Exception):
    """Raised when the conversation is not active."""


class SendMessageUseCase:
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
        self, *, user_id: str, conversation_id: str, command: SendMessageRequest
    ) -> MessageOrm:
        conversation = await self._repository.get_conversation(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError()
        member = await self._repository.get_member(conversation_id, user_id)
        if member is None or member.left_at is not None:
            raise NotMemberError()
        if conversation.status != ConversationStatus.ACTIVE:
            raise InvalidStateTransitionError()

        message = await self._repository.add_message(
            MessageOrm(
                conversation_id=conversation_id,
                sender_user_id=user_id,
                body=command.body,
            )
        )
        await self._publisher.publish("message.created.v1", message.id, user_id)
        await self._session.commit()
        return message
