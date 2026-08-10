"""Repository for the Presence context: pure data access, no business rules."""

import logging
from dataclasses import dataclass
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
from app.models.profile_photo import ProfilePhotoOrm
from app.models.trust import BlockOrm
from app.models.user import ProfileOrm, UserOrm, VerificationOrm
from app.models.venue import VenueOrm
from app.models.venue_check_in_token import VenueCheckInTokenOrm

logger = logging.getLogger(__name__)


@dataclass
class PresentProfile:
    """Present user with the data needed to build a safe public profile."""

    session: PresenceSessionOrm
    user: UserOrm
    profile: ProfileOrm
    photos: list[ProfilePhotoOrm]
    is_verified: bool


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

    def _visibility_conditions(self, venue_id: str, viewer_user_id: str | None, now: datetime) -> list:
        """Conditions shared by count and discovery queries (contract section 4.2)."""
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
        return conditions

    def _verified_user_ids_by(
        self, user_ids: select, now: datetime
    ) -> select:
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
        return verified_user_ids.where(VerificationOrm.user_id.in_(user_ids))

    async def count_visible_users(
        self, venue_id: str, viewer_user_id: str | None, now: datetime
    ) -> int:
        """Count users visible to the viewer at the venue at the given instant."""
        conditions = self._visibility_conditions(venue_id, viewer_user_id, now)

        verified_user_ids = self._verified_user_ids_by(select(ProfileOrm.user_id), now)
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

    async def list_visible_profiles(
        self,
        venue_id: str,
        viewer_user_id: str | None,
        now: datetime,
        limit: int,
        after: tuple[datetime, str] | None = None,
    ) -> tuple[list[PresentProfile], bool]:
        """Page of visible profiles ordered by check-in time then id.

        Returns (rows, has_more); the caller must strip the extra row.
        """
        conditions = self._visibility_conditions(venue_id, viewer_user_id, now)
        verified_user_ids = self._verified_user_ids_by(
            select(ProfileOrm.user_id), now
        )
        conditions.append(PresenceSessionOrm.user_id.in_(verified_user_ids))

        if after is not None:
            after_at, after_id = after
            conditions.append(
                or_(
                    PresenceSessionOrm.checked_in_at > after_at,
                    (PresenceSessionOrm.checked_in_at == after_at)
                    & (PresenceSessionOrm.id > after_id),
                )
            )

        stmt = (
            select(PresenceSessionOrm, UserOrm, ProfileOrm)
            .join(UserOrm, UserOrm.id == PresenceSessionOrm.user_id)
            .join(ProfileOrm, ProfileOrm.user_id == UserOrm.id)
            .where(*conditions)
            .order_by(
                PresenceSessionOrm.checked_in_at.asc(),
                PresenceSessionOrm.id.asc(),
            )
            .limit(limit + 1)
        )
        rows = (await self._session.execute(stmt)).all()
        has_more = len(rows) > limit
        rows = rows[:limit]

        user_ids = [row[1].id for row in rows]
        photos = await self._approved_photos(user_ids)
        verified = await self._user_ids_with_valid_verification(user_ids, now)
        logger.debug(
            "list_visible_profiles: venue=%s rows=%d has_more=%s users=%s",
            venue_id,
            len(rows),
            has_more,
            user_ids,
        )
        present = []
        for session, user, profile in rows:
            present.append(
                PresentProfile(
                    session=session,
                    user=user,
                    profile=profile,
                    photos=photos.get(user.id, []),
                    is_verified=user.id in verified,
                )
            )
        return present, has_more

    async def get_present_profile(
        self,
        venue_id: str,
        presence_id: str,
        viewer_user_id: str | None,
        now: datetime,
    ) -> PresentProfile | None:
        """A single profile visible to the viewer; None hides the target safely."""
        conditions = self._visibility_conditions(venue_id, viewer_user_id, now)
        conditions.append(PresenceSessionOrm.id == presence_id)

        verified_user_ids = self._verified_user_ids_by(select(ProfileOrm.user_id), now)
        conditions.append(PresenceSessionOrm.user_id.in_(verified_user_ids))

        stmt = (
            select(PresenceSessionOrm, UserOrm, ProfileOrm)
            .join(UserOrm, UserOrm.id == PresenceSessionOrm.user_id)
            .join(ProfileOrm, ProfileOrm.user_id == UserOrm.id)
            .where(*conditions)
        )
        row = (await self._session.execute(stmt)).one_or_none()
        if row is None:
            return None

        session, user, profile = row
        logger.debug(
            "get_present_profile: venue=%s presence=%s -> user=%s",
            venue_id,
            presence_id,
            user.id,
        )
        photos = await self._approved_photos([user.id])
        verified = user.id in await self._user_ids_with_valid_verification(
            [user.id], now
        )
        return PresentProfile(
            session=session,
            user=user,
            profile=profile,
            photos=photos.get(user.id, []),
            is_verified=verified,
        )

    async def _approved_photos(
        self, user_ids: list[str]
    ) -> dict[str, list[ProfilePhotoOrm]]:
        if not user_ids:
            return {}
        stmt = (
            select(ProfilePhotoOrm)
            .where(
                ProfilePhotoOrm.user_id.in_(user_ids),
                ProfilePhotoOrm.moderation_status == "approved",
                ProfilePhotoOrm.deleted_at.is_(None),
            )
            .order_by(ProfilePhotoOrm.user_id, ProfilePhotoOrm.position.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        by_user: dict[str, list[ProfilePhotoOrm]] = {}
        for photo in rows:
            by_user.setdefault(photo.user_id, []).append(photo)
        return by_user

    async def _user_ids_with_valid_verification(
        self, user_ids: list[str], now: datetime
    ) -> set[str]:
        if not user_ids:
            return set()
        stmt = (
            select(VerificationOrm.user_id)
            .where(
                VerificationOrm.user_id.in_(user_ids),
                VerificationOrm.status == VerificationStatus.APPROVED,
                or_(
                    VerificationOrm.expires_at.is_(None),
                    VerificationOrm.expires_at > now,
                ),
            )
            .distinct()
        )
        return set((await self._session.execute(stmt)).scalars().all())