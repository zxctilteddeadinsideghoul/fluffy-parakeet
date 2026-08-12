"""Use case: redeem a drink with the redemption code (contract 4.4)."""

import logging
from datetime import UTC, datetime
from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.drink import RedemptionOrm
from app.models.enums import DrinkOfferStatus, PaymentStatus, RedemptionStatus
from app.repositories.drink import DrinkRepository
from app.schemas.drink import RedeemDrinkRequest
from app.services.events import EventPublisher, event_publisher
from app.services.payments import PaymentGateway, payment_gateway

logger = logging.getLogger(__name__)


class RedemptionNotFoundError(Exception):
    """Raised when the code matches no redemption."""


class RedemptionExpiredError(Exception):
    """Raised when the redemption is already spent or past its expiration."""


class InvalidStateTransitionError(Exception):
    """Raised when the linked offer cannot be redeemed yet."""


class RedeemDrinkUseCase:
    """Redeems the code once and captures the payment."""

    def __init__(
        self,
        session: AsyncSession,
        repository: DrinkRepository,
        gateway: PaymentGateway = payment_gateway,
        publisher: EventPublisher = event_publisher,
    ) -> None:
        self._session = session
        self._repository = repository
        self._gateway = gateway
        self._publisher = publisher

    async def execute(
        self, *, user_id: str, command: RedeemDrinkRequest
    ) -> RedemptionOrm:
        now = datetime.now(UTC).replace(tzinfo=None)
        code_hash = sha256(command.redemption_code.encode()).hexdigest()
        redemption = await self._repository.get_redemption_by_code_hash(code_hash)
        if redemption is None:
            raise RedemptionNotFoundError()
        if redemption.status == RedemptionStatus.REDEEMED:
            logger.info(
                "redeem drink: idempotent replay code=%s redemption=%s",
                command.redemption_code,
                redemption.id,
            )
            return redemption

        offer = await self._repository.get_offer(redemption.drink_offer_id)
        if offer is None or offer.status != DrinkOfferStatus.ACCEPTED:
            raise InvalidStateTransitionError()
        if (
            redemption.status != RedemptionStatus.CREATED
            or redemption.expires_at <= now
        ):
            raise RedemptionExpiredError()

        payment = await self._repository.get_payment_by_offer(offer.id)
        if payment is None or payment.status != PaymentStatus.AUTHORIZED:
            raise InvalidStateTransitionError()

        await self._gateway.capture(provider_reference=payment.provider_reference or "")
        payment.status = PaymentStatus.CAPTURED
        payment.captured_at = now
        redemption.status = RedemptionStatus.REDEEMED
        redemption.redeemed_at = now
        redemption.venue_staff_id = user_id
        offer.status = DrinkOfferStatus.REDEEMED
        await self._session.flush()
        await self._publisher.publish("payment.captured.v1", offer.id, user_id)
        await self._publisher.publish("drink_offer.redeemed.v1", offer.id, user_id)
        await self._session.commit()
        return redemption
