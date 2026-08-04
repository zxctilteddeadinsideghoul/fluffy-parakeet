"""Shared test fixtures and factories."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.presence
import app.models.trust
import app.models.user
import app.models.venue
import app.models.venue_check_in_token
from app.api.presence import get_db
from app.main import app
from app.models.base import Base
from app.models.enums import (
    ApproachMode,
    CheckInMethod,
    PresenceStatus,
    PresenceVisibility,
    TokenStatus,
    UserStatus,
    VerificationStatus,
    VerificationType,
)
from app.models.presence import PresenceSession
from app.models.trust import Block
from app.models.user import Profile, User, Verification
from app.models.venue import Venue
from app.models.venue_check_in_token import VenueCheckInToken


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def create_user(
    db: Session,
    *,
    status: UserStatus = UserStatus.ACTIVE,
    verified: bool = True,
    profile_visible: bool = True,
) -> str:
    user = User(
        status=status,
        auth_provider="test",
        auth_subject=uuid.uuid4().hex,
        birth_date=date(2000, 1, 1),
    )
    db.add(user)
    db.flush()
    db.add(
        Profile(
            user_id=user.id,
            display_name=f"user-{user.id[:8]}",
            communication_goals="dating",
            default_approach_mode=ApproachMode.ASK_BEFORE_APPROACH,
            visibility_enabled=profile_visible,
        )
    )
    if verified:
        db.add(
            Verification(
                user_id=user.id,
                type=VerificationType.PHOTO,
                status=VerificationStatus.APPROVED,
                expires_at=utcnow() + timedelta(days=30),
            )
        )
    db.flush()
    return user.id


def create_venue(db: Session) -> str:
    venue = Venue(name="Bar", address="address", timezone="UTC")
    db.add(venue)
    db.flush()
    return venue.id


def create_session(
    db: Session,
    user_id: str,
    venue_id: str,
    *,
    status: PresenceStatus = PresenceStatus.ACTIVE,
    visibility: PresenceVisibility = PresenceVisibility.VISIBLE,
    expires_in: timedelta = timedelta(hours=2),
) -> str:
    session = PresenceSession(
        user_id=user_id,
        venue_id=venue_id,
        status=status,
        visibility=visibility,
        check_in_method=CheckInMethod.VENUE_QR,
        expires_at=utcnow() + expires_in,
    )
    db.add(session)
    db.flush()
    return session.id


def block_users(db: Session, blocker_id: str, blocked_id: str) -> None:
    db.add(Block(blocker_user_id=blocker_id, blocked_user_id=blocked_id))
    db.flush()


def create_token(
    db: Session,
    venue_id: str,
    *,
    raw_token: str = "secret-token",
    status: TokenStatus = TokenStatus.ACTIVE,
    valid_until: datetime | None = None,
) -> str:
    now = utcnow()
    db.add(
        VenueCheckInToken(
            venue_id=venue_id,
            token_hash=sha256(raw_token.encode()).hexdigest(),
            valid_from=now - timedelta(hours=1),
            valid_until=valid_until if valid_until is not None else now + timedelta(hours=1),
            status=status,
        )
    )
    db.flush()
    return raw_token
