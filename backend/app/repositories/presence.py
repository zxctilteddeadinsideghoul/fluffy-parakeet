"""Repository for the Presence context: pure data access, no business rules."""

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    PresenceStatus,
    PresenceVisibility,
    TokenStatus,
    UserStatus,
    VerificationStatus,
)
from app.models.presence import PresenceSessionOrm
from app.models.trust import BlockOrm
from app.models.user import ProfileOrm, UserOrm, VerificationOrm
from app.models.venue import VenueOrm
from app.models.venue_check_in_token import VenueCheckInTokenOrm


class PresenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def venue_exists(self, venue_id: str) -> bool:
        return await self._session.get(VenueOrm, venue_id) is not None

    async def venue_status(self, venue_id: str) -> str | None:
        venue = await self._session.get(VenueOrm, venue_id)
        return venue.status.value if venue is not None else None

    async def find_active_token(
        self, token_hash: str, now: datetime
    ) -> VenueCheckInTokenOrm | None:
        stmt = select(VenueCheckInTokenOrm).where(
            VenueCheckInTokenOrm.token_hash == token_hash,
            VenueCheckInTokenOrm.status == TokenStatus.ACTIVE,
            VenueCheckInTokenOrm.valid_from <= now,
            VenueCheckInTokenOrm.valid_until >= now,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def find_active_session(self, user_id: str) -> PresenceSessionOrm | None:
        stmt = select(PresenceSessionOrm).where(
            PresenceSessionOrm.user_id == user_id,
            PresenceSessionOrm.status.in_(
                [PresenceStatus.ACTIVE, PresenceStatus.HIDDEN]
            ),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

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

    async def user_status(self, user_id: str) -> UserStatus | None:
        user = await self._session.get(UserOrm, user_id)
        return user.status if user is not None else None

    async def add_session(self, session: PresenceSessionOrm) -> PresenceSessionOrm:
        self._session.add(session)
        await self._session.flush()
        await self._session.refresh(session)
        return session

    async def end_session(self, session: PresenceSessionOrm, now: datetime) -> PresenceSessionOrm:
        session.status = PresenceStatus.ENDED
        session.ended_at = now
        await self._session.flush()
        await self._session.refresh(session)
        return session

    async def count_visible_users(
        self, venue_id: str, viewer_user_id: str | None, now: datetime
    ) -> int:
        """Count users visible to the viewer at the venue at the given instant."""
        conditions = [
            PresenceSessionOrm.venue_id == venue_id,
            PresenceSessionOrm.status == PresenceStatus.ACTIVE,
            PresenceSessionOrm.visibility == PresenceVisibility.VISIBLE,
            PresenceSessionOrm.expires_at > now,
            UserOrm.status == UserStatus.ACTIVE,
            UserOrm.deleted_at.is_(None),
            ProfileOrm.visibility_enabled.is_(True),
        ]

        if viewer_user_id is not None:
            blocked_user_ids = select(BlockOrm.blocked_user_id).where(
                BlockOrm.blocker_user_id == viewer_user_id
            )
            blocked_user_ids = blocked_user_ids.union(
                select(BlockOrm.blocker_user_id).where(
                    BlockOrm.blocked_user_id == viewer_user_id
                )
            )
            conditions.append(PresenceSessionOrm.user_id != viewer_user_id)
            conditions.append(PresenceSessionOrm.user_id.not_in(blocked_user_ids))

        verified_user_ids = (
            select(VerificationOrm.user_id)
            .where(
                VerificationOrm.status == VerificationStatus.APPROVED,
                or_(
                    VerificationOrm.expires_at.is_(None),
                    VerificationOrm.expires_at > now,
                ),
            )
            .distinct()
        )
        conditions.append(PresenceSessionOrm.user_id.in_(verified_user_ids))

        visible_user_ids = (
            select(PresenceSessionOrm.user_id)
            .join(UserOrm, UserOrm.id == PresenceSessionOrm.user_id)
            .join(ProfileOrm, ProfileOrm.user_id == UserOrm.id)
            .where(*conditions)
            .distinct()
        )

        count_stmt = select(func.count()).select_from(visible_user_ids.subquery())
        return int((await self._session.execute(count_stmt)).scalar_one())