"""Shared test fixtures and factories."""

import tempfile
import uuid
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from pathlib import Path

import pytest
from dependency_injector import providers
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models.drink
import app.models.presence
import app.models.profile_photo
import app.models.trust
import app.models.user
import app.models.venue
import app.models.venue_check_in_token
from app.core.db import Base, get_db_session
from app.main import app
from app.models.drink import MenuItemOrm
from app.models.enums import (
    ApproachMode,
    AvailabilityStatus,
    CheckInMethod,
    MediaModerationStatus,
    PresenceStatus,
    PresenceVisibility,
    TokenStatus,
    UserStatus,
    VerificationStatus,
    VerificationType,
)
from app.models.presence import PresenceSessionOrm
from app.models.profile_photo import ProfilePhotoOrm
from app.models.trust import BlockOrm
from app.models.user import ProfileOrm, UserOrm, VerificationOrm
from app.models.venue import VenueOrm
from app.models.venue_check_in_token import VenueCheckInTokenOrm
from app.storage.local import LocalPhotoStorage

TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest.fixture()
async def db_session():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest.fixture()
async def client(db_session):
    async def override_get_db():
        yield db_session

    with tempfile.TemporaryDirectory() as media_dir:
        app.container.photo_storage.override(  # type: ignore[attr-defined]
            providers.Object(LocalPhotoStorage(Path(media_dir)))
        )
        app.dependency_overrides[get_db_session] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()
        app.container.photo_storage.reset_override()  # type: ignore[attr-defined]


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def create_user(
    session,
    *,
    status: UserStatus = UserStatus.ACTIVE,
    verified: bool = True,
    profile_visible: bool = True,
    display_name: str | None = None,
    bio: str | None = None,
    birth_date: date | None = date(2000, 1, 1),
) -> str:
    user = UserOrm(
        status=status,
        auth_provider="test",
        auth_subject=uuid.uuid4().hex,
        birth_date=birth_date,
    )
    session.add(user)
    await session.flush()
    session.add(
        ProfileOrm(
            user_id=user.id,
            display_name=display_name or f"user-{user.id[:8]}",
            bio=bio,
            communication_goals="dating",
            default_approach_mode=ApproachMode.ASK_BEFORE_APPROACH,
            visibility_enabled=profile_visible,
        )
    )
    if verified:
        session.add(
            VerificationOrm(
                user_id=user.id,
                type=VerificationType.PHOTO,
                status=VerificationStatus.APPROVED,
                expires_at=utcnow() + timedelta(days=30),
            )
        )
    await session.flush()
    return user.id


async def create_venue(session) -> str:
    venue = VenueOrm(name="Bar", address="address", timezone="UTC")
    session.add(venue)
    await session.flush()
    return venue.id


async def create_session(
    session,
    user_id: str,
    venue_id: str,
    *,
    status: PresenceStatus = PresenceStatus.ACTIVE,
    visibility: PresenceVisibility = PresenceVisibility.VISIBLE,
    approach_mode: ApproachMode = ApproachMode.ASK_BEFORE_APPROACH,
    expires_in: timedelta = timedelta(hours=2),
) -> str:
    presence = PresenceSessionOrm(
        user_id=user_id,
        venue_id=venue_id,
        status=status,
        visibility=visibility,
        approach_mode=approach_mode,
        check_in_method=CheckInMethod.VENUE_QR,
        expires_at=utcnow() + expires_in,
    )
    session.add(presence)
    await session.flush()
    return presence.id


async def block_users(session, blocker_id: str, blocked_id: str) -> None:
    session.add(BlockOrm(blocker_user_id=blocker_id, blocked_user_id=blocked_id))
    await session.flush()


async def create_token(
    session,
    venue_id: str,
    *,
    raw_token: str = "secret-token",
    status: TokenStatus = TokenStatus.ACTIVE,
    valid_until: datetime | None = None,
) -> str:
    now = utcnow()
    session.add(
        VenueCheckInTokenOrm(
            venue_id=venue_id,
            token_hash=sha256(raw_token.encode()).hexdigest(),
            valid_from=now - timedelta(hours=1),
            valid_until=valid_until if valid_until is not None else now + timedelta(hours=1),
            status=status,
        )
    )
    await session.flush()
    return raw_token


async def create_photo(
    session,
    user_id: str,
    *,
    position: int = 0,
    url: str = "https://cdn.example.com/photo.jpg",
    moderation: MediaModerationStatus = MediaModerationStatus.APPROVED,
) -> str:
    photo = ProfilePhotoOrm(
        user_id=user_id,
        storage_key=f"key-{user_id[:8]}-{position}",
        public_url=url,
        position=position,
        moderation_status=moderation,
    )
    session.add(photo)
    await session.flush()
    return photo.id


async def create_menu_item(
    session,
    venue_id: str,
    *,
    name: str = "Negroni",
    price_minor: int = 350,
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE,
) -> str:
    item = MenuItemOrm(
        venue_id=venue_id,
        name=name,
        price_minor=price_minor,
        currency="RUB",
        availability_status=availability,
    )
    session.add(item)
    await session.flush()
    return item.id
