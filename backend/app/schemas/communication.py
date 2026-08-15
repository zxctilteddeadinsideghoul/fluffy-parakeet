"""Public DTOs for the Communication context (requests, connections, chats).

Aligned with docs/CONTRACTS_DATA.md sections 4.3 and 6. Fields are snake_case
in Python and serialized as camelCase by the ApiModel alias generator.
"""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.enums import ConversationStatus, MessageType, RequestStatus
from app.schemas.base import ApiModel


class SendContactRequestRequest(ApiModel):
    recipient_presence_id: str
    message: str | None = Field(default=None, max_length=500)


class ContactRequestDto(ApiModel):
    id: str
    sender_user_id: str
    recipient_user_id: str
    sender_presence_id: str
    recipient_presence_id: str
    venue_id: str
    status: RequestStatus
    message: str | None = None
    created_at: datetime
    responded_at: datetime | None = None
    expires_at: datetime


class RespondContactRequestRequest(ApiModel):
    decision: Literal["accept", "decline"]


class ConversationDto(ApiModel):
    id: str
    connection_id: str
    status: ConversationStatus
    peer_user_id: str
    created_at: datetime
    last_message_body: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = Field(ge=0)


class SendMessageRequest(ApiModel):
    body: str = Field(min_length=1, max_length=2000)


class MessageDto(ApiModel):
    id: str
    conversation_id: str
    sender_user_id: str
    type: MessageType
    body: str
    created_at: datetime


class MessagesPageDto(ApiModel):
    items: list[MessageDto]
    next_cursor: str | None = None
