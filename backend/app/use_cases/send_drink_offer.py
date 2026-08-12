"""Use case: send a drink offer from the venue menu (contract 4.4)."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.drink import DrinkOfferOrm, PaymentOrm
from app.models.enums import (
    AvailabilityStatus,
    DrinkOfferStatus,
    PaymentStatus,
    PresenceStatus,
    UserStatus,
)
from app.repositories.drink import DrinkRepository
from app.schemas.drink import SendDrinkOfferRequest
from app.services.events import EventPublisher, event_publisher
from app.services.payments import PaymentGateway, payment_gateway
from app.services.policy import drink_offer_allowed

logger = logging.getLogger(__name__)


class UserNotActiveError(Exception):
    """Raised when the sender account is not active."""


class VerificationRequiredError(Exception):
    """Raised when the sender has no valid verification."""


class NoActivePresenceError(Exception):
    """Raised when the sender has no active presence session."""


class RecipientNotPresentError(Exception):
    """Raised when the recipient presence is not active at the same venue."""


class NotSameVenueError(Exception):
    """Raised when the recipient presence belongs to another venue."""


class SelfInteractionError(Exception):
    """Raised when the sender tries to send a drink to themselves."""


class BlockedError(Exception):
    """Raised when either side has blocked the other."""


class ConnectionRequiredError(Exception):
    """Raised when product policy demands an active connection first."""


class MenuItemNotFoundError(Exception):
    """Raised when the menu item does not exist."""


class MenuItemUnavailableError(Exception):
    """Raised when the menu item is not sellable at the sender's venue."""


class SendDrinkOfferUseCase:
    """Authorizes payment and creates a drink offer for a present recipient."""

    def __init__(
        self,
        session: AsyncSession,
        repository: DrinkRepository,
        offer_ttl_minutes: int = settings.drink_offer_ttl_minutes,
        requires_connection: bool = settings.drink_offer_requires_connection,
        gateway: PaymentGateway = payment_gateway,
        publisher: EventPublisher = event_publisher,
    ) -> None:
        self._session = session
        self._repository = repository
        self._offer_ttl_minutes = offer_ttl_minutes
        self._requires_connection = requires_connection
        self._gateway = gateway
        self._publisher = publisher

    async def execute(self, *, user_id: str, command: SendDrinkOfferRequest) -> DrinkOfferOrm:
        now = datetime.now(UTC).replace(tzinfo=None)
        sender_session = await self._repository.find_active_session(user_id, now)
        if sender_session is None:
            raise NoActivePresenceError()
        if await self._repository.user_status(user_id) != UserStatus.ACTIVE:
            raise UserNotActiveError(user_id)
        if not await self._repository.is_verified_user(user_id, now):
            raise VerificationRequiredError(user_id)

        payment = await self._repository.get_payment_by_idempotency(
            user_id, command.idempotency_key
        )
        if payment is not None:
            logger.info(
                "send drink offer: idempotent replay payer=%s payment=%s",
                user_id,
                payment.id,
            )
            return await self._repository.get_offer(payment.drink_offer_id)

        recipient_session = await self._repository.get_session(command.recipient_presence_id)
        if recipient_session is None:
            raise RecipientNotPresentError()
        if (
            recipient_session.status != PresenceStatus.ACTIVE
            or recipient_session.expires_at <= now
            or recipient_session.venue_id != sender_session.venue_id
        ):
            raise NotSameVenueError()
        recipient_user_id = recipient_session.user_id
        if recipient_user_id == user_id:
            raise SelfInteractionError()
        if await self._repository.has_block_between(user_id, recipient_user_id):
            raise BlockedError()
        if not drink_offer_allowed(self._requires_connection):
            raise ConnectionRequiredError()

        menu_item = await self._repository.get_menu_item(command.menu_item_id)
        if menu_item is None:
            raise MenuItemNotFoundError()
        if (
            menu_item.venue_id != sender_session.venue_id
            or menu_item.availability_status != AvailabilityStatus.AVAILABLE
        ):
            raise MenuItemUnavailableError()

        logger.info(
            "send drink offer: sender=%s recipient=%s venue=%s item=%s",
            user_id,
            recipient_user_id,
            sender_session.venue_id,
            menu_item.id,
        )
        provider_reference = await self._gateway.authorize(
            idempotency_key=command.idempotency_key
        )
        offer = await self._repository.add_offer(
            DrinkOfferOrm(
                sender_user_id=user_id,
                recipient_user_id=recipient_user_id,
                sender_presence_id=sender_session.id,
                recipient_presence_id=recipient_session.id,
                venue_id=sender_session.venue_id,
                menu_item_id=menu_item.id,
                status=DrinkOfferStatus.PAYMENT_AUTHORIZED,
                item_name_snapshot=menu_item.name,
                price_minor_snapshot=menu_item.price_minor,
                currency_snapshot=menu_item.currency,
                expires_at=now + timedelta(minutes=self._offer_ttl_minutes),
            )
        )
        await self._repository.add_payment(
            PaymentOrm(
                drink_offer_id=offer.id,
                payer_user_id=user_id,
                amount_minor=menu_item.price_minor,
                currency=menu_item.currency,
                provider=self._gateway.provider,
                provider_reference=provider_reference,
                idempotency_key=command.idempotency_key,
                status=PaymentStatus.AUTHORIZED,
                authorized_at=now,
            )
        )
        await self._publisher.publish("payment.authorized.v1", offer.id, user_id)
        await self._publisher.publish("drink_offer.created.v1", offer.id, user_id)
        await self._session.commit()
        return offer
