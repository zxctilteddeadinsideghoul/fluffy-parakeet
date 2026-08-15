"""Use case: list the current user's conversations (chat list)."""

import logging

from app.repositories.communication import CommunicationRepository
from app.schemas.communication import ConversationDto

logger = logging.getLogger(__name__)


class ListConversationsUseCase:
    """Returns the user's chats with the peer and the last message."""

    def __init__(self, repository: CommunicationRepository) -> None:
        self._repository = repository

    async def execute(self, *, user_id: str) -> list[ConversationDto]:
        conversations = await self._repository.list_conversations_for_user(user_id)
        result = []
        for conversation in conversations:
            peer_id = await self._repository.peer_user_id(conversation, user_id)
            if peer_id is None:
                continue
            member = await self._repository.get_member(conversation.id, user_id)
            last = await self._repository.last_message(conversation.id)
            unread = 0
            if member is not None:
                unread = await self._repository.unread_count(conversation.id, member)
            result.append(
                ConversationDto(
                    id=conversation.id,
                    connection_id=conversation.connection_id,
                    status=conversation.status,
                    peer_user_id=peer_id,
                    created_at=conversation.created_at,
                    last_message_body=last.body if last is not None else None,
                    last_message_at=last.created_at if last is not None else None,
                    unread_count=unread,
                )
            )
        return result
