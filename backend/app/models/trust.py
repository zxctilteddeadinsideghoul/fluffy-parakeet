"""Block model (Trust & Safety context)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class Block(Base):
    __tablename__ = "blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    blocker_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    blocked_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    reason_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
