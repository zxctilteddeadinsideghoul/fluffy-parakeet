"""Tests for presence check-in and check-out use cases."""

from datetime import timedelta

import pytest

from app.models.enums import (
    ApproachMode,
    CheckInMethod,
    PresenceStatus,
    PresenceVisibility,
    TokenStatus,
    UserStatus,
)
from app.repositories.presence import PresenceRepository
from app.schemas.presence import CheckInRequest
from app.use_cases.check_in import (
    CheckInUseCase,
    InvalidCheckInTokenError,
    PresenceAlreadyActiveError,
    UserNotActiveError,
    VerificationRequiredError,
)
from app.use_cases.check_out import CheckOutUseCase, PresenceNotActiveError
from tests.conftest import create_token, create_user, create_venue, utcnow


def check_in_command(raw_token: str = "secret-token") -> CheckInRequest:
    return CheckInRequest(
        venue_token=raw_token,
        visibility=PresenceVisibility.VISIBLE,
        approach_mode=ApproachMode.ASK_BEFORE_APPROACH,
    )


async def check_in(session, user_id: str, command: CheckInRequest, ttl_hours: int = 4):
    return await CheckInUseCase(
        session, PresenceRepository(session), ttl_hours=ttl_hours
    ).execute(user_id=user_id, command=command)


async def check_out(session, user_id: str):
    return await CheckOutUseCase(
        session, PresenceRepository(session)
    ).execute(user_id=user_id)


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, str | None]] = []

    async def publish(
        self, event_type: str, entity_id: str, actor_user_id: str | None = None
    ) -> None:
        self.events.append((event_type, entity_id, actor_user_id))


async def test_check_in_creates_active_session(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session)
    await create_token(db_session, venue_id)

    session = await check_in(db_session, user_id, check_in_command())

    assert session.user_id == user_id
    assert session.venue_id == venue_id
    assert session.status == PresenceStatus.ACTIVE
    assert session.visibility == PresenceVisibility.VISIBLE
    assert session.approach_mode == ApproachMode.ASK_BEFORE_APPROACH
    assert session.check_in_method == CheckInMethod.VENUE_QR
    assert session.expires_at > utcnow()


async def test_check_in_respects_requested_visibility(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session)
    await create_token(db_session, venue_id)

    command = CheckInRequest(
        venue_token="secret-token",
        visibility=PresenceVisibility.HIDDEN,
        approach_mode=ApproachMode.CHAT_ONLY,
    )
    session = await check_in(db_session, user_id, command)

    assert session.visibility == PresenceVisibility.HIDDEN
    assert session.approach_mode == ApproachMode.CHAT_ONLY


async def test_check_in_rejects_unknown_token(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session)
    await create_token(db_session, venue_id)

    with pytest.raises(InvalidCheckInTokenError):
        await check_in(db_session, user_id, check_in_command(raw_token="wrong-token"))


async def test_check_in_rejects_revoked_token(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session)
    await create_token(db_session, venue_id, status=TokenStatus.REVOKED)

    with pytest.raises(InvalidCheckInTokenError):
        await check_in(db_session, user_id, check_in_command())


async def test_check_in_rejects_expired_token(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session)
    await create_token(
        db_session, venue_id, valid_until=utcnow() - timedelta(minutes=1)
    )

    with pytest.raises(InvalidCheckInTokenError):
        await check_in(db_session, user_id, check_in_command())


async def test_check_in_rejects_unverified_user(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session, verified=False)
    await create_token(db_session, venue_id)

    with pytest.raises(VerificationRequiredError):
        await check_in(db_session, user_id, check_in_command())


async def test_check_in_rejects_suspended_user(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session, status=UserStatus.SUSPENDED)
    await create_token(db_session, venue_id)

    with pytest.raises(UserNotActiveError):
        await check_in(db_session, user_id, check_in_command())


async def test_check_in_rejects_second_active_session(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session)
    await create_token(db_session, venue_id)

    await check_in(db_session, user_id, check_in_command())
    with pytest.raises(PresenceAlreadyActiveError):
        await check_in(db_session, user_id, check_in_command())


async def test_check_out_ends_active_session(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session)
    await create_token(db_session, venue_id)
    started = await check_in(db_session, user_id, check_in_command())

    session = await check_out(db_session, user_id)

    assert session.id == started.id
    assert session.status == PresenceStatus.ENDED
    assert session.ended_at is not None


async def test_check_out_without_active_session_raises(db_session):
    user_id = await create_user(db_session)

    with pytest.raises(PresenceNotActiveError):
        await check_out(db_session, user_id)


async def test_check_in_publishes_started_event(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session)
    await create_token(db_session, venue_id)
    publisher = RecordingPublisher()

    session = await CheckInUseCase(
        db_session, PresenceRepository(db_session), publisher=publisher
    ).execute(user_id=user_id, command=check_in_command())

    assert publisher.events == [("presence.started.v1", session.id, user_id)]


async def test_check_out_publishes_ended_event(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session)
    await create_token(db_session, venue_id)
    await check_in(db_session, user_id, check_in_command())
    publisher = RecordingPublisher()

    ended = await CheckOutUseCase(
        db_session, PresenceRepository(db_session), publisher=publisher
    ).execute(user_id=user_id)

    assert publisher.events == [("presence.ended.v1", ended.id, user_id)]