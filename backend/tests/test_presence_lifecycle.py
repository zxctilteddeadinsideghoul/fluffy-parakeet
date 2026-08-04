"""Use case tests for presence check-in and check-out."""

from datetime import timedelta

import pytest

from app.models.enums import (
    ApproachMode,
    PresenceStatus,
    PresenceVisibility,
    TokenStatus,
)
from app.repositories.presence import PresenceRepository
from app.schemas.presence import CheckInCommand
from app.services.presence import (
    CheckInUseCase,
    CheckOutUseCase,
    InvalidCheckInTokenError,
    PresenceAlreadyActiveError,
    PresenceNotActiveError,
    VerificationRequiredError,
)
from tests.conftest import create_session, create_token, create_user, create_venue, utcnow


def check_in_command(raw_token: str = "secret-token") -> CheckInCommand:
    return CheckInCommand(
        venue_token=raw_token,
        visibility=PresenceVisibility.VISIBLE,
        approach_mode=ApproachMode.ASK_BEFORE_APPROACH,
    )


def check_in(db, user_id: str, command: CheckInCommand):
    return CheckInUseCase(PresenceRepository(db), ttl_hours=4).execute(user_id, command)


def check_out(db, user_id: str):
    return CheckOutUseCase(PresenceRepository(db)).execute(user_id)


def test_check_in_creates_active_session(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)

    dto = check_in(db_session, user_id, check_in_command())

    assert dto.venue_id == venue_id
    assert dto.status == PresenceStatus.ACTIVE
    assert dto.visibility == PresenceVisibility.VISIBLE
    assert dto.approach_mode == ApproachMode.ASK_BEFORE_APPROACH
    assert dto.expires_at > utcnow()


def test_check_in_respects_requested_visibility(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)

    command = CheckInCommand(
        venue_token="secret-token",
        visibility=PresenceVisibility.HIDDEN,
        approach_mode=ApproachMode.CHAT_ONLY,
    )
    dto = check_in(db_session, user_id, command)

    assert dto.visibility == PresenceVisibility.HIDDEN
    assert dto.approach_mode == ApproachMode.CHAT_ONLY


def test_check_in_rejects_unknown_token(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)

    with pytest.raises(InvalidCheckInTokenError):
        check_in(db_session, user_id, check_in_command(raw_token="wrong-token"))


def test_check_in_rejects_revoked_token(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id, status=TokenStatus.REVOKED)

    with pytest.raises(InvalidCheckInTokenError):
        check_in(db_session, user_id, check_in_command())


def test_check_in_rejects_expired_token(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id, valid_until=utcnow() - timedelta(minutes=1))

    with pytest.raises(InvalidCheckInTokenError):
        check_in(db_session, user_id, check_in_command())


def test_check_in_rejects_unverified_user(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session, verified=False)
    create_token(db_session, venue_id)

    with pytest.raises(VerificationRequiredError):
        check_in(db_session, user_id, check_in_command())


def test_check_in_rejects_second_session(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    check_in(db_session, user_id, check_in_command())

    with pytest.raises(PresenceAlreadyActiveError):
        check_in(db_session, user_id, check_in_command())


def test_check_out_ends_session(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    check_in(db_session, user_id, check_in_command())

    dto = check_out(db_session, user_id)

    assert dto.status == PresenceStatus.ENDED


def test_check_out_requires_active_session(db_session):
    with pytest.raises(PresenceNotActiveError):
        check_out(db_session, create_user(db_session))


def test_check_out_ends_hidden_session_too(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    create_session(
        db_session,
        user_id,
        venue_id,
        visibility=PresenceVisibility.HIDDEN,
    )

    dto = check_out(db_session, user_id)

    assert dto.status == PresenceStatus.ENDED
