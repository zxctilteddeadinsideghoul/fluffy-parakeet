"""ProfilePhoto ORM model (Identity context)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import MediaModerationStatus


def new_uuid() -> str:
    return str(uuid.uuid4())


class ProfilePhotoOrm(Base):
    __tablename__ = "profile_photos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    storage_key: Mapped[str] = mapped_column(String(500))
    public_url: Mapped[str | None] = mapped_column(String(1000))
    position: Mapped[int] = mapped_column(Integer, default=0)
    moderation_status: Mapped[MediaModerationStatus] = mapped_column(
        Enum(
            MediaModerationStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=MediaModerationStatus.APPROVED,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
