"""User, Profile and Verification ORM models (Identity context)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import (
    ApproachMode,
    UserStatus,
    VerificationStatus,
    VerificationType,
)

NATIVE_ENUM = False


def new_uuid() -> str:
    return str(uuid.uuid4())


class UserOrm(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("auth_provider", "auth_subject", name="uq_users_auth_identity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=NATIVE_ENUM, values_callable=lambda e: [m.value for m in e]),
        default=UserStatus.ACTIVE,
    )
    phone_normalized: Mapped[str | None] = mapped_column(String(32))
    email_normalized: Mapped[str | None] = mapped_column(String(254))
    auth_provider: Mapped[str] = mapped_column(String(64))
    auth_subject: Mapped[str] = mapped_column(String(255))
    birth_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped[ProfileOrm | None] = relationship(back_populates="user", uselist=False)


class ProfileOrm(Base):
    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str | None] = mapped_column(String(32))
    bio: Mapped[str | None] = mapped_column(String(1000))
    communication_goals: Mapped[str] = mapped_column(String(500))
    default_approach_mode: Mapped[ApproachMode] = mapped_column(
        Enum(
            ApproachMode,
            native_enum=NATIVE_ENUM,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ApproachMode.ASK_BEFORE_APPROACH,
    )
    visibility_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped[UserOrm] = relationship(back_populates="profile")


class VerificationOrm(Base):
    __tablename__ = "verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    type: Mapped[VerificationType] = mapped_column(
        Enum(
            VerificationType,
            native_enum=NATIVE_ENUM,
            values_callable=lambda e: [m.value for m in e],
        )
    )
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(
            VerificationStatus,
            native_enum=NATIVE_ENUM,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=VerificationStatus.PENDING,
    )
    provider_reference: Mapped[str | None] = mapped_column(String(255))
    rejection_reason_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))