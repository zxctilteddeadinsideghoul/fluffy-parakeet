"""Use case: list the available menu of a venue."""

import logging

from app.repositories.drink import DrinkRepository
from app.schemas.drink import MenuItemDto

logger = logging.getLogger(__name__)


class VenueNotFoundError(Exception):
    """Raised when the venue does not exist."""


class ListVenueMenuUseCase:
    """Returns the sellable menu items of a venue."""

    def __init__(self, repository: DrinkRepository) -> None:
        self._repository = repository

    async def execute(self, *, venue_id: str) -> list[MenuItemDto]:
        if not await self._repository.venue_exists(venue_id):
            raise VenueNotFoundError()
        items = await self._repository.list_available_menu(venue_id)
        return [
            MenuItemDto(
                id=item.id,
                venue_id=item.venue_id,
                name=item.name,
                description=item.description,
                price={"amount_minor": item.price_minor, "currency": item.currency},
                image_url=item.image_url,
                availability_status=item.availability_status,
            )
            for item in items
        ]
