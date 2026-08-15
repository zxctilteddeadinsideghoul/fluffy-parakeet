"""Public DTOs for the Commerce context (drink offers, payments, redemptions).

Aligned with docs/CONTRACTS_DATA.md sections 2, 4.4 and 6: Money is never a
float, payment-changing commands carry an idempotencyKey, success responses
are wrapped in the ResponseEnvelope by the routes. Fields are snake_case in
Python and serialized as camelCase by the ApiModel alias generator.
"""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.enums import AvailabilityStatus, DrinkOfferStatus, RedemptionStatus
from app.schemas.base import ApiModel


class MoneyDto(ApiModel):
    amount_minor: int = Field(ge=0)
    currency: str


class MenuItemDto(ApiModel):
    id: str
    venue_id: str
    name: str
    description: str | None = None
    price: MoneyDto
    image_url: str | None = None
    availability_status: AvailabilityStatus


class DrinkOfferDto(ApiModel):
    id: str
    sender_user_id: str
    sender_display_name: str
    recipient_user_id: str
    recipient_display_name: str
    sender_presence_id: str
    recipient_presence_id: str
    venue_id: str
    menu_item_id: str
    connection_id: str | None = None
    status: DrinkOfferStatus
    item_name_snapshot: str
    price_snapshot: MoneyDto
    created_at: datetime
    responded_at: datetime | None = None
    expires_at: datetime


class SendDrinkOfferRequest(ApiModel):
    recipient_presence_id: str
    menu_item_id: str
    idempotency_key: str = Field(min_length=1)


class RespondToDrinkOfferRequest(ApiModel):
    decision: Literal["accept", "decline"]


class RedeemDrinkRequest(ApiModel):
    redemption_code: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)


class RedemptionCreatedDto(ApiModel):
    id: str
    drink_offer_id: str
    code: str
    status: RedemptionStatus
    expires_at: datetime


class RedemptionDto(ApiModel):
    id: str
    drink_offer_id: str
    status: RedemptionStatus
    expires_at: datetime
    redeemed_at: datetime | None = None


class DrinkOfferResponseDto(ApiModel):
    offer: DrinkOfferDto
    redemption: RedemptionCreatedDto | None = None
