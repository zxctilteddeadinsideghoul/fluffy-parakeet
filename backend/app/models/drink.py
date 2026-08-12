"""Drink, payment and redemption ORM models (Commerce context).

Aligned with docs/CONTRACTS_DATA.md sections 4.4 and 9: snapshots,
UNIQUE drinkOfferId on Payment/Redemption, UNIQUE (payerUserId,
idempotencyKey) on Payment, CHECK actor != recipient, CHECK amountMinor >= 0.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import AvailabilityStatus, DrinkOfferStatus, PaymentStatus, RedemptionStatus


def new_uuid() -> str:
    return str(uuid.uuid4())


class MenuItemOrm(Base):
    __tablename__ = "menu_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000))
    price_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    image_url: Mapped[str | None] = mapped_column(String(1000))
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(
            AvailabilityStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=AvailabilityStatus.AVAILABLE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (CheckConstraint("price_minor >= 0", name="ck_menu_price_minor"),)


class DrinkOfferOrm(Base):
    __tablename__ = "drink_offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    sender_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    recipient_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    sender_presence_id: Mapped[str] = mapped_column(ForeignKey("presence_sessions.id"))
    recipient_presence_id: Mapped[str] = mapped_column(ForeignKey("presence_sessions.id"))
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id"), index=True)
    menu_item_id: Mapped[str] = mapped_column(ForeignKey("menu_items.id"))
    connection_id: Mapped[str | None] = mapped_column(String(36))
    status: Mapped[DrinkOfferStatus] = mapped_column(
        Enum(
            DrinkOfferStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=DrinkOfferStatus.PAYMENT_AUTHORIZED,
    )
    item_name_snapshot: Mapped[str] = mapped_column(String(200))
    price_minor_snapshot: Mapped[int] = mapped_column(Integer)
    currency_snapshot: Mapped[str] = mapped_column(String(3), default="RUB")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("sender_user_id != recipient_user_id", name="ck_drink_actor_not_recipient"),
        CheckConstraint("price_minor_snapshot >= 0", name="ck_drink_price_snapshot"),
    )


class PaymentOrm(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    drink_offer_id: Mapped[str] = mapped_column(
        ForeignKey("drink_offers.id"), unique=True
    )
    payer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    provider: Mapped[str] = mapped_column(String(64))
    provider_reference: Mapped[str | None] = mapped_column(String(256))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=PaymentStatus.CREATED,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String(64))

    __table_args__ = (
        UniqueConstraint("payer_user_id", "idempotency_key", name="uq_payment_idempotency"),
        CheckConstraint("amount_minor >= 0", name="ck_payment_amount_minor"),
    )


class RedemptionOrm(Base):
    __tablename__ = "redemptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    drink_offer_id: Mapped[str] = mapped_column(
        ForeignKey("drink_offers.id"), unique=True
    )
    code_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[RedemptionStatus] = mapped_column(
        Enum(
            RedemptionStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=RedemptionStatus.CREATED,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    venue_staff_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
