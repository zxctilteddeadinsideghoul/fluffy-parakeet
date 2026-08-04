"""Use case tests for presence check-in and check-out."""

from datetime import timedelta

import pytest

from app.models.enums import (
    ApproachMode,
    PresenceStatus,
    PresenceVisibility,
    TokenStatus,
    UserStatus,
    VenueStatus,
)
from app.models.presence import PresenceSession
from app.models.venue import Venue
from app.repositories.presence import PresenceRepository
from app.schemas.presence import CheckInCommand
from app.services.presence import (
    CheckInUseCase,
    CheckOutUseCase,
    CountPresentUsersUseCase,
    InvalidCheckInTokenError,
    PresenceAlreadyActiveError,
    PresenceNotActiveError,
    UserNotActiveError,
    VenueNotFoundError,
    VerificationRequiredError,
)
from tests.conftest import create_session, create_token, create_user, create_venue, utcnow


def check_in_command(raw_token: str = "secret-token") -> CheckInCommand:
    return CheckInCommand(
        venue_token=raw_token,
        visibility=PresenceVisibility.VISIBLE,
        approach_mode=ApproachMode.ASK_BEFORE_APPROACH,
    )


def check_in(db, user_id: str, command: CheckInCommand, ttl_hours: int = 4):
    return CheckInUseCase(PresenceRepository(db), ttl_hours=ttl_hours).execute(user_id, command)


def check_out(db, user_id: str):
    return CheckOutUseCase(PresenceRepository(db)).execute(user_id)


def count_present(db, venue_id: str) -> int:
    return CountPresentUsersUseCase(PresenceRepository(db)).execute(venue_id)


class RecordingPublisher:
    def __init__(self):
        self.events: list[tuple[str, str, str | None]] = []

    def publish(self, event_type: str, entity_id: str, actor_user_id: str | None = None) -> None:
        self.events.append((event_type, entity_id, actor_user_id))


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


def test_check_in_rejects_suspended_user(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session, status=UserStatus.SUSPENDED)
    create_token(db_session, venue_id)

    with pytest.raises(UserNotActiveError):
        check_in(db_session, user_id, check_in_command())


def test_check_in_rejects_unknown_user(db_session):
    venue_id = create_venue(db_session)
    create_token(db_session, venue_id)

    with pytest.raises(UserNotActiveError):
        check_in(db_session, "no-such-user", check_in_command())


def test_check_in_rejects_token_of_inactive_venue(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    venue = db_session.get(Venue, venue_id)
    venue.status = VenueStatus.INACTIVE
    db_session.flush()

    with pytest.raises(VenueNotFoundError):
        check_in(db_session, user_id, check_in_command())


def test_check_in_rejects_second_session(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    check_in(db_session, user_id, check_in_command())

    with pytest.raises(PresenceAlreadyActiveError):
        check_in(db_session, user_id, check_in_command())


def test_check_in_applies_configured_ttl(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)

    dto = check_in(db_session, user_id, check_in_command(), ttl_hours=2)

    expected = utcnow() + timedelta(hours=2)
    assert abs((dto.expires_at - expected).total_seconds()) < 60


def test_check_in_persists_session(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)

    check_in(db_session, user_id, check_in_command())

    persisted = PresenceRepository(db_session).find_active_session(user_id)
    assert persisted is not None
    assert persisted.venue_id == venue_id


def test_check_in_publishes_started_event(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    publisher = RecordingPublisher()

    dto = CheckInUseCase(PresenceRepository(db_session), ttl_hours=4, publisher=publisher).execute(
        user_id, check_in_command()
    )

    assert publisher.events == [("presence.started.v1", dto.id, user_id)]


def test_checked_in_visible_user_is_counted(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)

    check_in(db_session, user_id, check_in_command())

    assert count_present(db_session, venue_id) == 1


def test_checked_in_hidden_user_is_not_counted(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    check_in(db_session, user_id, check_in_command())

    hidden_command = CheckInCommand(
        venue_token="secret-token",
        visibility=PresenceVisibility.HIDDEN,
        approach_mode=ApproachMode.CHAT_ONLY,
    )
    check_in(db_session, create_user(db_session), hidden_command)

    assert count_present(db_session, venue_id) == 1


def test_check_out_ends_session(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    check_in(db_session, user_id, check_in_command())

    dto = check_out(db_session, user_id)

    assert dto.status == PresenceStatus.ENDED


def test_check_out_sets_ended_at(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    check_in(db_session, user_id, check_in_command())

    dto = check_out(db_session, user_id)

    session = db_session.get(PresenceSession, dto.id)
    assert session.ended_at is not None


def test_check_out_requires_active_session(db_session):
    with pytest.raises(PresenceNotActiveError):
        check_out(db_session, create_user(db_session))


def test_check_out_rejects_repeat(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    check_in(db_session, user_id, check_in_command())
    check_out(db_session, user_id)

    with pytest.raises(PresenceNotActiveError):
        check_out(db_session, user_id)


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


def test_check_out_ends_expired_but_active_session(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_session(db_session, user_id, venue_id, expires_in=timedelta(hours=-1))

    dto = check_out(db_session, user_id)

    assert dto.status == PresenceStatus.ENDED


def test_check_out_allows_new_check_in_after(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    check_in(db_session, user_id, check_in_command())
    check_out(db_session, user_id)

    dto = check_in(db_session, user_id, check_in_command())

    assert dto.status == PresenceStatus.ACTIVE


def test_checked_out_user_is_not_counted(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    check_in(db_session, user_id, check_in_command())

    check_out(db_session, user_id)

    assert count_present(db_session, venue_id) == 0


def test_check_out_publishes_ended_event(db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    check_in(db_session, user_id, check_in_command())
    publisher = RecordingPublisher()

    dto = CheckOutUseCase(PresenceRepository(db_session), publisher=publisher).execute(user_id)

    assert publisher.events == [("presence.ended.v1", dto.id, user_id)]
