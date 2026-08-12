"""Use case: page of messages in a conversation."""

import base64
import json
import logging
from datetime import datetime

from app.repositories.communication import CommunicationRepository
from app.schemas.communication import MessageDto, MessagesPageDto

logger = logging.getLogger(__name__)


class ConversationNotFoundError(Exception):
    """Raised when the conversation does not exist or is hidden from the user."""


class InvalidCursorError(Exception):
    """Raised when the pagination cursor cannot be parsed."""


def encode_cursor(created_at: datetime, message_id: str) -> str:
    payload = json.dumps({"t": created_at.isoformat(), "id": message_id})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        data = json.loads(raw)
        return datetime.fromisoformat(data["t"]), str(data["id"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise InvalidCursorError() from None


class ListMessagesUseCase:
    def __init__(self, repository: CommunicationRepository) -> None:
        self._repository = repository

    async def execute(
        self, *, user_id: str, conversation_id: str, limit: int, cursor: str | None
    ) -> MessagesPageDto:
        conversation = await self._repository.get_conversation(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError()
        member = await self._repository.get_member(conversation_id, user_id)
        if member is None:
            raise ConversationNotFoundError()

        after = decode_cursor(cursor) if cursor is not None else None
        messages, has_more = await self._repository.list_messages(
            conversation_id, limit=limit, after=after
        )
        items = [
            MessageDto(
                id=message.id,
                conversation_id=message.conversation_id,
                sender_user_id=message.sender_user_id,
                type=message.type,
                body=message.body,
                created_at=message.created_at,
            )
            for message in messages
        ]
        next_cursor = None
        if has_more and messages:
            last = messages[-1]
            next_cursor = encode_cursor(last.created_at, last.id)
        return MessagesPageDto(items=items, next_cursor=next_cursor)
