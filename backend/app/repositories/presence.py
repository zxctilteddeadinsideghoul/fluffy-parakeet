"""Repository for the Presence context: pure data access, no business rules."""

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import (
    PresenceStatus,
    PresenceVisibility,
    TokenStatus,
    UserStatus,
    VerificationStatus,
)
from app.models.presence import PresenceSession
from app.models.trust import Block
from app.models.user import Profile, User, Verification
from app.models.venue import Venue
from app.models.venue_check_in_token import VenueCheckInToken


class PresenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def venue_exists(self, venue_id: str) -> bool:
        return self.db.get(Venue, venue_id) is not None

    def find_active_token(self, token_hash: str, now: datetime) -> VenueCheckInToken | None:
        stmt = select(VenueCheckInToken).where(
            VenueCheckInToken.token_hash == token_hash,
            VenueCheckInToken.status == TokenStatus.ACTIVE,
            VenueCheckInToken.valid_from <= now,
            VenueCheckInToken.valid_until >= now,
        )
        return self.db.scalar(stmt)

    def find_active_session(self, user_id: str) -> PresenceSession | None:
        stmt = select(PresenceSession).where(
            PresenceSession.user_id == user_id,
            PresenceSession.status.in_([PresenceStatus.ACTIVE, PresenceStatus.HIDDEN]),
        )
        return self.db.scalar(stmt)

    def is_verified_user(self, user_id: str, now: datetime) -> bool:
        stmt = (
            select(Verification.user_id)
            .where(
                Verification.user_id == user_id,
                Verification.status == VerificationStatus.APPROVED,
                or_(Verification.expires_at.is_(None), Verification.expires_at > now),
            )
            .limit(1)
        )
        return self.db.scalar(stmt) is not None

    def user_status(self, user_id: str) -> UserStatus | None:
        user = self.db.get(User, user_id)
        return user.status if user is not None else None

    def add_session(self, session: PresenceSession) -> PresenceSession:
        self.db.add(session)
        self.db.flush()
        return session

    def venue_status(self, venue_id: str) -> str | None:
        venue = self.db.get(Venue, venue_id)
        return venue.status.value if venue is not None else None

    def count_visible_users(self, venue_id: str, viewer_user_id: str | None, now: datetime) -> int:
        """Count users visible to the viewer at the venue at the given instant."""
        conditions = [
            PresenceSession.venue_id == venue_id,
            PresenceSession.status == PresenceStatus.ACTIVE,
            PresenceSession.visibility == PresenceVisibility.VISIBLE,
            PresenceSession.expires_at > now,
            User.status == UserStatus.ACTIVE,
            User.deleted_at.is_(None),
            Profile.visibility_enabled.is_(True),
        ]

        if viewer_user_id is not None:
            blocked_user_ids = select(Block.blocked_user_id).where(
                Block.blocker_user_id == viewer_user_id
            )
            blocked_user_ids = blocked_user_ids.union(
                select(Block.blocker_user_id).where(Block.blocked_user_id == viewer_user_id)
            )
            conditions.append(PresenceSession.user_id != viewer_user_id)
            conditions.append(PresenceSession.user_id.not_in(blocked_user_ids))

        verified_user_ids = (
            select(Verification.user_id)
            .where(
                Verification.status == VerificationStatus.APPROVED,
                or_(Verification.expires_at.is_(None), Verification.expires_at > now),
            )
            .distinct()
        )
        conditions.append(PresenceSession.user_id.in_(verified_user_ids))

        visible_user_ids = (
            select(PresenceSession.user_id)
            .join(User, User.id == PresenceSession.user_id)
            .join(Profile, Profile.user_id == User.id)
            .where(*conditions)
            .distinct()
        )

        count_stmt = select(func.count()).select_from(visible_user_ids.subquery())
        return int(self.db.scalar(count_stmt))
