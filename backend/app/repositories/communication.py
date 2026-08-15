"""Repository for the Communication context: pure data access, no business rules."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import (
    ConnectionOrm,
    ContactRequestOrm,
    ConversationMemberOrm,
    ConversationOrm,
    MessageOrm,
)
from app.models.enums import (
    PresenceStatus,
    UserStatus,
    VerificationStatus,
)
from app.models.presence import PresenceSessionOrm
from app.models.trust import BlockOrm
from app.models.user import VerificationOrm


class CommunicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def user_status(self, user_id: str) -> UserStatus | None:
        from app.models.user import UserOrm

        user = await self._session.get(UserOrm, user_id)
        return user.status if user is not None else None

    async def is_verified_user(self, user_id: str, now: datetime) -> bool:
        stmt = (
            select(VerificationOrm.user_id)
            .where(
                VerificationOrm.user_id == user_id,
                VerificationOrm.status == VerificationStatus.APPROVED,
                or_(
                    VerificationOrm.expires_at.is_(None),
                    VerificationOrm.expires_at > now,
                ),
            )
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    async def find_active_session(self, user_id: str, now: datetime) -> PresenceSessionOrm | None:
        stmt = select(PresenceSessionOrm).where(
            PresenceSessionOrm.user_id == user_id,
            PresenceSessionOrm.status.in_([PresenceStatus.ACTIVE, PresenceStatus.HIDDEN]),
            PresenceSessionOrm.expires_at > now,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_session(self, session_id: str) -> PresenceSessionOrm | None:
        return await self._session.get(PresenceSessionOrm, session_id)

    async def has_block_between(self, user_a: str, user_b: str) -> bool:
        stmt = select(BlockOrm.id).where(
            or_(
                (BlockOrm.blocker_user_id == user_a) & (BlockOrm.blocked_user_id == user_b),
                (BlockOrm.blocker_user_id == user_b) & (BlockOrm.blocked_user_id == user_a),
            )
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    async def find_duplicate_request(
        self, sender_user_id: str, recipient_user_id: str, recipient_presence_id: str
    ) -> ContactRequestOrm | None:
        stmt = select(ContactRequestOrm).where(
            ContactRequestOrm.sender_user_id == sender_user_id,
            ContactRequestOrm.recipient_user_id == recipient_user_id,
            ContactRequestOrm.recipient_presence_id == recipient_presence_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_request(self, request_id: str) -> ContactRequestOrm | None:
        return await self._session.get(ContactRequestOrm, request_id)

    async def list_requests_for_user(self, user_id: str) -> list[ContactRequestOrm]:
        stmt = (
            select(ContactRequestOrm)
            .where(
                or_(
                    ContactRequestOrm.sender_user_id == user_id,
                    ContactRequestOrm.recipient_user_id == user_id,
                )
            )
            .order_by(ContactRequestOrm.created_at.desc(), ContactRequestOrm.id.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def add_request(self, request: ContactRequestOrm) -> ContactRequestOrm:
        self._session.add(request)
        await self._session.flush()
        await self._session.refresh(request)
        return request

    async def add_connection(self, connection: ConnectionOrm) -> ConnectionOrm:
        self._session.add(connection)
        await self._session.flush()
        await self._session.refresh(connection)
        return connection

    async def add_conversation(self, conversation: ConversationOrm) -> ConversationOrm:
        self._session.add(conversation)
        await self._session.flush()
        await self._session.refresh(conversation)
        return conversation

    async def add_member(self, member: ConversationMemberOrm) -> ConversationMemberOrm:
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def get_conversation(self, conversation_id: str) -> ConversationOrm | None:
        return await self._session.get(ConversationOrm, conversation_id)

    async def get_member(
        self, conversation_id: str, user_id: str
    ) -> ConversationMemberOrm | None:
        stmt = select(ConversationMemberOrm).where(
            ConversationMemberOrm.conversation_id == conversation_id,
            ConversationMemberOrm.user_id == user_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_conversations_for_user(self, user_id: str) -> list[ConversationOrm]:
        stmt = (
            select(ConversationOrm)
            .join(
                ConversationMemberOrm,
                ConversationMemberOrm.conversation_id == ConversationOrm.id,
            )
            .where(ConversationMemberOrm.user_id == user_id)
            .order_by(ConversationOrm.created_at.desc(), ConversationOrm.id.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def peer_user_id(self, conversation: ConversationOrm, me: str) -> str | None:
        stmt = select(ConversationMemberOrm.user_id).where(
            ConversationMemberOrm.conversation_id == conversation.id,
            ConversationMemberOrm.user_id != me,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def last_message(self, conversation_id: str) -> MessageOrm | None:
        stmt = (
            select(MessageOrm)
            .where(
                MessageOrm.conversation_id == conversation_id,
                MessageOrm.deleted_at.is_(None),
            )
            .order_by(MessageOrm.created_at.desc(), MessageOrm.id.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def unread_count(self, conversation_id: str, member: ConversationMemberOrm) -> int:
        if member.last_read_message_id is None:
            stmt = select(func.count(MessageOrm.id)).where(
                MessageOrm.conversation_id == conversation_id,
                MessageOrm.sender_user_id != member.user_id,
                MessageOrm.deleted_at.is_(None),
            )
            return int((await self._session.execute(stmt)).scalar_one())
        last_read_at = (
            select(MessageOrm.created_at)
            .where(MessageOrm.id == member.last_read_message_id)
            .scalar_subquery()
        )
        stmt = select(func.count(MessageOrm.id)).where(
            MessageOrm.conversation_id == conversation_id,
            MessageOrm.sender_user_id != member.user_id,
            MessageOrm.created_at > last_read_at,
            MessageOrm.deleted_at.is_(None),
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def add_message(self, message: MessageOrm) -> MessageOrm:
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def list_messages(
        self,
        conversation_id: str,
        limit: int,
        after: tuple[datetime, str] | None = None,
    ) -> tuple[list[MessageOrm], bool]:
        stmt = select(MessageOrm).where(
            MessageOrm.conversation_id == conversation_id,
            MessageOrm.deleted_at.is_(None),
        )
        if after is not None:
            after_at, after_id = after
            stmt = stmt.where(
                or_(
                    MessageOrm.created_at > after_at,
                    (MessageOrm.created_at == after_at) & (MessageOrm.id > after_id),
                )
            )
        stmt = stmt.order_by(MessageOrm.created_at.asc(), MessageOrm.id.asc()).limit(limit + 1)
        rows = (await self._session.execute(stmt)).scalars().all()
        has_more = len(rows) > limit
        return list(rows[:limit]), has_more
