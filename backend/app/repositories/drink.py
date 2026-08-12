"""Repository for the Commerce context: pure data access, no business rules."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.drink import DrinkOfferOrm, MenuItemOrm, PaymentOrm, RedemptionOrm
from app.models.enums import (
    AvailabilityStatus,
    PresenceStatus,
    UserStatus,
    VerificationStatus,
)
from app.models.presence import PresenceSessionOrm
from app.models.trust import BlockOrm
from app.models.user import VerificationOrm


class DrinkRepository:
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

    async def venue_exists(self, venue_id: str) -> bool:
        from app.models.venue import VenueOrm

        return await self._session.get(VenueOrm, venue_id) is not None

    async def get_menu_item(self, menu_item_id: str) -> MenuItemOrm | None:
        return await self._session.get(MenuItemOrm, menu_item_id)

    async def list_available_menu(self, venue_id: str) -> list[MenuItemOrm]:
        stmt = (
            select(MenuItemOrm)
            .where(
                MenuItemOrm.venue_id == venue_id,
                MenuItemOrm.availability_status == AvailabilityStatus.AVAILABLE,
            )
            .order_by(MenuItemOrm.name.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_offer(self, offer_id: str) -> DrinkOfferOrm | None:
        return await self._session.get(DrinkOfferOrm, offer_id)

    async def list_offers_for_user(self, user_id: str) -> list[DrinkOfferOrm]:
        stmt = (
            select(DrinkOfferOrm)
            .where(
                or_(
                    DrinkOfferOrm.sender_user_id == user_id,
                    DrinkOfferOrm.recipient_user_id == user_id,
                )
            )
            .order_by(DrinkOfferOrm.created_at.desc(), DrinkOfferOrm.id.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_payment_by_idempotency(
        self, payer_user_id: str, idempotency_key: str
    ) -> PaymentOrm | None:
        stmt = select(PaymentOrm).where(
            PaymentOrm.payer_user_id == payer_user_id,
            PaymentOrm.idempotency_key == idempotency_key,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_payment_by_offer(self, drink_offer_id: str) -> PaymentOrm | None:
        stmt = select(PaymentOrm).where(PaymentOrm.drink_offer_id == drink_offer_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_redemption_by_code_hash(self, code_hash: str) -> RedemptionOrm | None:
        stmt = select(RedemptionOrm).where(RedemptionOrm.code_hash == code_hash)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add_offer(self, offer: DrinkOfferOrm) -> DrinkOfferOrm:
        self._session.add(offer)
        await self._session.flush()
        await self._session.refresh(offer)
        return offer

    async def add_payment(self, payment: PaymentOrm) -> PaymentOrm:
        self._session.add(payment)
        await self._session.flush()
        await self._session.refresh(payment)
        return payment

    async def add_redemption(self, redemption: RedemptionOrm) -> RedemptionOrm:
        self._session.add(redemption)
        await self._session.flush()
        await self._session.refresh(redemption)
        return redemption
