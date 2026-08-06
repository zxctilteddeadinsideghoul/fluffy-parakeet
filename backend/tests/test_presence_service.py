"""Use case tests for counting present users at a venue."""

from datetime import timedelta

import pytest

from app.models.enums import PresenceStatus, PresenceVisibility, UserStatus
from app.repositories.presence import PresenceRepository
from app.use_cases.count_present_users import CountPresentUsersUseCase, VenueNotFoundError
from tests.conftest import block_users, create_session, create_user, create_venue


async def count(session, venue_id: str, viewer_user_id: str | None = None) -> int:
    return await CountPresentUsersUseCase(PresenceRepository(session)).execute(
        venue_id=venue_id, viewer_user_id=viewer_user_id
    )


async def test_returns_zero_when_no_sessions(db_session):
    venue_id = await create_venue(db_session)
    assert await count(db_session, venue_id) == 0


async def test_counts_only_active_visible_sessions_in_venue(db_session):
    venue_id = await create_venue(db_session)
    other_venue_id = await create_venue(db_session)
    for _ in range(3):
        await create_session(db_session, await create_user(db_session), venue_id)
    await create_session(db_session, await create_user(db_session), other_venue_id)
    await create_session(
        db_session, await create_user(db_session), venue_id, status=PresenceStatus.ENDED
    )
    await create_session(
        db_session,
        await create_user(db_session),
        venue_id,
        visibility=PresenceVisibility.HIDDEN,
    )
    await create_session(
        db_session,
        await create_user(db_session),
        venue_id,
        expires_in=timedelta(hours=-1),
    )
    assert await count(db_session, venue_id) == 3


async def test_excludes_unverified_users(db_session):
    venue_id = await create_venue(db_session)
    await create_session(db_session, await create_user(db_session), venue_id)
    await create_session(
        db_session, await create_user(db_session, verified=False), venue_id
    )
    assert await count(db_session, venue_id) == 1


async def test_excludes_users_with_hidden_profile(db_session):
    venue_id = await create_venue(db_session)
    await create_session(db_session, await create_user(db_session), venue_id)
    await create_session(
        db_session, await create_user(db_session, profile_visible=False), venue_id
    )
    assert await count(db_session, venue_id) == 1


async def test_excludes_inactive_users(db_session):
    venue_id = await create_venue(db_session)
    await create_session(db_session, await create_user(db_session), venue_id)
    await create_session(
        db_session,
        await create_user(db_session, status=UserStatus.SUSPENDED),
        venue_id,
    )
    assert await count(db_session, venue_id) == 1


async def test_viewer_does_not_count_itself(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, await create_user(db_session), venue_id)
    await create_session(db_session, viewer_id, venue_id)
    assert await count(db_session, venue_id, viewer_user_id=viewer_id) == 1


async def test_viewer_excludes_users_blocked_by_viewer(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    other_id = await create_user(db_session)
    await create_session(db_session, other_id, venue_id)
    await block_users(db_session, viewer_id, other_id)
    assert await count(db_session, venue_id, viewer_user_id=viewer_id) == 0


async def test_viewer_excludes_users_who_blocked_viewer(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    other_id = await create_user(db_session)
    await create_session(db_session, other_id, venue_id)
    await block_users(db_session, other_id, viewer_id)
    assert await count(db_session, venue_id, viewer_user_id=viewer_id) == 0


async def test_raises_for_unknown_venue(db_session):
    with pytest.raises(VenueNotFoundError):
        await count(db_session, "no-such-venue")