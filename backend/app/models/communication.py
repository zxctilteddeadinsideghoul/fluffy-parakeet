"""Contact, connection, conversation and message ORM models.

Aligned with docs/CONTRACTS_DATA.md section 4.3 and 9: accepting a
ContactRequest atomically creates one Connection, one Conversation and two
ConversationMembers; UNIQUE sourceRequestId on Connection, UNIQUE
connectionId on Conversation, UNIQUE (conversationId, userId) on
ConversationMember, UNIQUE (senderUserId, recipientUserId,
recipientPresenceId) on ContactRequest, CHECK actor != recipient.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import (
    ConnectionStatus,
    ConversationStatus,
    MessageType,
    RequestStatus,
)


def new_uuid() -> str:
    return str(uuid.uuid4())


class ContactRequestOrm(Base):
    __tablename__ = "contact_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    sender_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    recipient_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    sender_presence_id: Mapped[str] = mapped_column(ForeignKey("presence_sessions.id"))
    recipient_presence_id: Mapped[str] = mapped_column(ForeignKey("presence_sessions.id"))
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id"), index=True)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(
            RequestStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=RequestStatus.PENDING,
    )
    message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint(
            "sender_user_id",
            "recipient_user_id",
            "recipient_presence_id",
            name="uq_contact_request_visit",
        ),
        CheckConstraint(
            "sender_user_id != recipient_user_id", name="ck_contact_actor_not_recipient"
        ),
    )


class ConnectionOrm(Base):
    __tablename__ = "connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_a_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    user_b_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id"), index=True)
    source_request_id: Mapped[str] = mapped_column(
        ForeignKey("contact_requests.id"), unique=True
    )
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(
            ConnectionStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ConnectionStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("user_a_id != user_b_id", name="ck_connection_actor_not_recipient"),
    )


class ConversationOrm(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    connection_id: Mapped[str] = mapped_column(
        ForeignKey("connections.id"), unique=True
    )
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(
            ConversationStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ConversationStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConversationMemberOrm(Base):
    __tablename__ = "conversation_members"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    last_read_message_id: Mapped[str | None] = mapped_column(String(36))
    muted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("conversation_id", "user_id", name="uq_member_pair"),)


class MessageOrm(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    type: Mapped[MessageType] = mapped_column(
        Enum(
            MessageType,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=MessageType.TEXT,
    )
    body: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
