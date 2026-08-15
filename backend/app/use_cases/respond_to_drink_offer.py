"""Use case: accept or decline a received drink offer (contract 4.4)."""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.drink import DrinkOfferOrm, RedemptionOrm
from app.models.enums import DrinkOfferStatus, PaymentStatus, RedemptionStatus
from app.repositories.drink import DrinkRepository
from app.services.events import EventPublisher, event_publisher
from app.services.payments import PaymentGateway, payment_gateway

logger = logging.getLogger(__name__)

RespondDecision = Literal["accept", "decline"]


class OfferNotFoundError(Exception):
    """Raised when the offer does not exist or belongs to another user."""


class OfferExpiredError(Exception):
    """Raised when the offer is past its expiration."""


class InvalidStateTransitionError(Exception):
    """Raised when the offer is not waiting for a response."""


class RespondToDrinkOfferUseCase:
    """Accepts (creates the redemption code) or declines (voids the payment)."""

    def __init__(
        self,
        session: AsyncSession,
        repository: DrinkRepository,
        redemption_ttl_minutes: int = settings.redemption_ttl_minutes,
        gateway: PaymentGateway = payment_gateway,
        publisher: EventPublisher = event_publisher,
    ) -> None:
        self._session = session
        self._repository = repository
        self._redemption_ttl_minutes = redemption_ttl_minutes
        self._gateway = gateway
        self._publisher = publisher

    async def execute(
        self, *, user_id: str, offer_id: str, decision: RespondDecision
    ) -> tuple[DrinkOfferOrm, RedemptionOrm | None, str | None]:
        now = datetime.now(UTC).replace(tzinfo=None)
        offer = await self._repository.get_offer(offer_id)
        if offer is None or offer.recipient_user_id != user_id:
            raise OfferNotFoundError()
        if offer.status not in (
            DrinkOfferStatus.PAYMENT_AUTHORIZED,
            DrinkOfferStatus.PENDING,
        ):
            raise InvalidStateTransitionError()
        if offer.expires_at <= now:
            raise OfferExpiredError()

        payment = await self._repository.get_payment_by_offer(offer.id)
        if payment is None:
            raise InvalidStateTransitionError()

        offer.responded_at = now
        if decision == "decline":
            await self._gateway.void(provider_reference=payment.provider_reference or "")
            payment.status = PaymentStatus.VOIDED
            payment.voided_at = now
            offer.status = DrinkOfferStatus.DECLINED
            await self._session.flush()
            await self._publisher.publish("payment.voided.v1", offer.id, user_id)
            await self._publisher.publish("drink_offer.declined.v1", offer.id, user_id)
            await self._session.commit()
            return offer, None, None

        offer.status = DrinkOfferStatus.ACCEPTED
        code = _generate_code()
        redemption = await self._repository.add_redemption(
            RedemptionOrm(
                drink_offer_id=offer.id,
                code_hash=sha256(code.encode()).hexdigest(),
                status=RedemptionStatus.CREATED,
                expires_at=now + timedelta(minutes=self._redemption_ttl_minutes),
            )
        )
        await self._session.flush()
        await self._publisher.publish("drink_offer.accepted.v1", offer.id, user_id)
        await self._session.commit()
        return offer, redemption, code


def _generate_code() -> str:
    """Six-digit numeric code shown to the recipient once, after acceptance."""
    return f"{secrets.randbelow(1_000_000):06d}"
