"""Use case tests for counting present users at a venue."""

from datetime import timedelta

import pytest

from app.models.enums import PresenceStatus, PresenceVisibility, UserStatus
from app.repositories.presence import PresenceRepository
from app.services.presence import CountPresentUsersUseCase, VenueNotFoundError
from tests.conftest import block_users, create_session, create_user, create_venue


def count(db, venue_id: str, viewer_user_id: str | None = None) -> int:
    return CountPresentUsersUseCase(PresenceRepository(db)).execute(venue_id, viewer_user_id)


def test_returns_zero_when_no_sessions(db_session):
    venue_id = create_venue(db_session)
    assert count(db_session, venue_id) == 0


def test_counts_only_active_visible_sessions_in_venue(db_session):
    venue_id = create_venue(db_session)
    other_venue_id = create_venue(db_session)
    for _ in range(3):
        create_session(db_session, create_user(db_session), venue_id)
    create_session(db_session, create_user(db_session), other_venue_id)
    create_session(
        db_session,
        create_user(db_session),
        venue_id,
        status=PresenceStatus.ENDED,
    )
    create_session(
        db_session,
        create_user(db_session),
        venue_id,
        visibility=PresenceVisibility.HIDDEN,
    )
    create_session(
        db_session,
        create_user(db_session),
        venue_id,
        expires_in=timedelta(hours=-1),
    )
    assert count(db_session, venue_id) == 3


def test_excludes_unverified_users(db_session):
    venue_id = create_venue(db_session)
    create_session(db_session, create_user(db_session), venue_id)
    create_session(db_session, create_user(db_session, verified=False), venue_id)
    assert count(db_session, venue_id) == 1


def test_excludes_users_with_hidden_profile(db_session):
    venue_id = create_venue(db_session)
    create_session(db_session, create_user(db_session), venue_id)
    create_session(db_session, create_user(db_session, profile_visible=False), venue_id)
    assert count(db_session, venue_id) == 1


def test_excludes_inactive_users(db_session):
    venue_id = create_venue(db_session)
    create_session(db_session, create_user(db_session), venue_id)
    create_session(db_session, create_user(db_session, status=UserStatus.SUSPENDED), venue_id)
    assert count(db_session, venue_id) == 1


def test_viewer_does_not_count_itself(db_session):
    venue_id = create_venue(db_session)
    viewer_id = create_user(db_session)
    create_session(db_session, create_user(db_session), venue_id)
    create_session(db_session, viewer_id, venue_id)
    assert count(db_session, venue_id, viewer_user_id=viewer_id) == 1


def test_viewer_excludes_users_blocked_by_viewer(db_session):
    venue_id = create_venue(db_session)
    viewer_id = create_user(db_session)
    other_id = create_user(db_session)
    create_session(db_session, other_id, venue_id)
    block_users(db_session, viewer_id, other_id)
    assert count(db_session, venue_id, viewer_user_id=viewer_id) == 0


def test_viewer_excludes_users_who_blocked_viewer(db_session):
    venue_id = create_venue(db_session)
    viewer_id = create_user(db_session)
    other_id = create_user(db_session)
    create_session(db_session, other_id, venue_id)
    block_users(db_session, other_id, viewer_id)
    assert count(db_session, venue_id, viewer_user_id=viewer_id) == 0


def test_raises_for_unknown_venue(db_session):
    with pytest.raises(VenueNotFoundError):
        count(db_session, "no-such-venue")
