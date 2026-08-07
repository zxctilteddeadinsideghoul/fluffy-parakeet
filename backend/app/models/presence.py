"""PresenceSession ORM model (Presence context)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import (
    ApproachMode,
    CheckInMethod,
    PresenceStatus,
    PresenceVisibility,
)


def new_uuid() -> str:
    return str(uuid.uuid4())


class PresenceSessionOrm(Base):
    __tablename__ = "presence_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id"), index=True)
    status: Mapped[PresenceStatus] = mapped_column(
        Enum(
            PresenceStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=PresenceStatus.ACTIVE,
    )
    visibility: Mapped[PresenceVisibility] = mapped_column(
        Enum(
            PresenceVisibility,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=PresenceVisibility.VISIBLE,
    )
    approach_mode: Mapped[ApproachMode] = mapped_column(
        Enum(
            ApproachMode,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ApproachMode.ASK_BEFORE_APPROACH,
    )
    check_in_method: Mapped[CheckInMethod] = mapped_column(
        Enum(
            CheckInMethod,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        )
    )
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))