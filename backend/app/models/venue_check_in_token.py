"""Venue check-in token ORM model (Venue context)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import TokenStatus


def new_uuid() -> str:
    return str(uuid.uuid4())


class VenueCheckInTokenOrm(Base):
    __tablename__ = "venue_check_in_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[TokenStatus] = mapped_column(
        Enum(TokenStatus, native_enum=False, values_callable=lambda e: [m.value for m in e]),
        default=TokenStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)