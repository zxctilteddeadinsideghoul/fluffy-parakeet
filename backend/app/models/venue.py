"""Venue ORM model (Venue context)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import VenuePartnerStatus, VenueStatus


def new_uuid() -> str:
    return str(uuid.uuid4())


class VenueOrm(Base):
    __tablename__ = "venues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(String(500))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    status: Mapped[VenueStatus] = mapped_column(
        Enum(VenueStatus, native_enum=False, values_callable=lambda e: [m.value for m in e]),
        default=VenueStatus.ACTIVE,
    )
    partner_status: Mapped[VenuePartnerStatus] = mapped_column(
        Enum(
            VenuePartnerStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=VenuePartnerStatus.PROSPECT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )