"""Use case: list the current user's drink offers with their statuses."""

import logging

from app.repositories.drink import DrinkRepository
from app.schemas.drink import DrinkOfferDto

logger = logging.getLogger(__name__)


def offer_to_dto(offer) -> DrinkOfferDto:
    return DrinkOfferDto(
        id=offer.id,
        sender_user_id=offer.sender_user_id,
        recipient_user_id=offer.recipient_user_id,
        sender_presence_id=offer.sender_presence_id,
        recipient_presence_id=offer.recipient_presence_id,
        venue_id=offer.venue_id,
        menu_item_id=offer.menu_item_id,
        connection_id=offer.connection_id,
        status=offer.status,
        item_name_snapshot=offer.item_name_snapshot,
        price_snapshot={
            "amount_minor": offer.price_minor_snapshot,
            "currency": offer.currency_snapshot,
        },
        created_at=offer.created_at,
        responded_at=offer.responded_at,
        expires_at=offer.expires_at,
    )


class ListMyDrinkOffersUseCase:
    """Returns offers the user sent or received, newest first."""

    def __init__(self, repository: DrinkRepository) -> None:
        self._repository = repository

    async def execute(self, *, user_id: str) -> list[DrinkOfferDto]:
        offers = await self._repository.list_offers_for_user(user_id)
        return [offer_to_dto(offer) for offer in offers]
