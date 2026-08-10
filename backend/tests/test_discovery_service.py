"""Use case tests for listing present profiles and getting a full profile."""

import pytest

from app.models.enums import (
    ApproachMode,
    MediaModerationStatus,
    PresenceStatus,
    PresenceVisibility,
    UserStatus,
)
from app.repositories.presence import PresenceRepository
from app.use_cases.get_present_profile import (
    GetPresentProfileUseCase,
    ProfileNotFoundError,
)
from app.use_cases.list_present_profiles import (
    ListPresentProfilesUseCase,
    VenueNotFoundError,
    ViewerNotPresentError,
)
from tests.conftest import (
    block_users,
    create_photo,
    create_session,
    create_user,
    create_venue,
)


async def list_profiles(
    session,
    venue_id: str,
    viewer_user_id: str,
    *,
    limit: int = 20,
    cursor: str | None = None,
):
    return await ListPresentProfilesUseCase(PresenceRepository(session)).execute(
        venue_id=venue_id,
        viewer_user_id=viewer_user_id,
        limit=limit,
        cursor=cursor,
    )


async def get_profile(session, presence_id: str, viewer_user_id: str):
    return await GetPresentProfileUseCase(PresenceRepository(session)).execute(
        presence_id=presence_id, viewer_user_id=viewer_user_id
    )


async def test_list_returns_visible_profiles(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session, display_name="Viewer")
    await create_session(db_session, viewer_id, venue_id)
    other_id = await create_user(db_session, display_name="Anna")
    await create_session(db_session, other_id, venue_id)
    await create_photo(db_session, other_id, position=0, url="https://cdn/1.jpg")

    items, next_cursor = await list_profiles(db_session, venue_id, viewer_id)

    assert next_cursor is None
    assert len(items) == 1
    profile = items[0]
    assert profile.userId == other_id
    assert profile.displayName == "Anna"
    assert profile.age >= 26
    assert profile.photos[0].url == "https://cdn/1.jpg"
    assert profile.isVerified is True
    assert "contact" in profile.availableActions


async def test_list_returns_null_age_when_birth_date_missing(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    other_id = await create_user(db_session, birth_date=None)
    await create_session(db_session, other_id, venue_id)

    items, _ = await list_profiles(db_session, venue_id, viewer_id)

    assert len(items) == 1
    assert items[0].age is None


async def test_list_excludes_hidden_expired_and_ended_sessions(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    for _ in range(2):
        await create_session(db_session, await create_user(db_session), venue_id)
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
        status=PresenceStatus.ENDED,
    )

    items, _ = await list_profiles(db_session, venue_id, viewer_id)

    assert len(items) == 2


async def test_list_excludes_self(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)

    items, _ = await list_profiles(db_session, venue_id, viewer_id)

    assert items == []


async def test_list_excludes_blocked_users_in_both_directions(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    blocked_id = await create_user(db_session)
    await create_session(db_session, blocked_id, venue_id)
    blocker_id = await create_user(db_session)
    await create_session(db_session, blocker_id, venue_id)
    await block_users(db_session, viewer_id, blocked_id)
    await block_users(db_session, blocker_id, viewer_id)

    items, _ = await list_profiles(db_session, venue_id, viewer_id)

    assert items == []


async def test_list_excludes_inactive_and_hidden_profile_users(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    await create_session(
        db_session,
        await create_user(db_session, status=UserStatus.SUSPENDED),
        venue_id,
    )
    await create_session(
        db_session, await create_user(db_session, profile_visible=False), venue_id
    )

    items, _ = await list_profiles(db_session, venue_id, viewer_id)

    assert items == []


async def test_photos_are_sorted_and_approved_only(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    other_id = await create_user(db_session)
    await create_session(db_session, other_id, venue_id)
    await create_photo(db_session, other_id, position=1, url="https://cdn/2.jpg")
    await create_photo(
        db_session,
        other_id,
        position=0,
        url="https://cdn/1.jpg",
        moderation=MediaModerationStatus.PENDING,
    )

    items, _ = await list_profiles(db_session, venue_id, viewer_id)

    assert [p.url for p in items[0].photos] == ["https://cdn/2.jpg"]


async def test_list_requires_viewer_presence_in_same_venue(db_session):
    venue_id = await create_venue(db_session)
    other_venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, other_venue_id)

    with pytest.raises(ViewerNotPresentError):
        await list_profiles(db_session, venue_id, viewer_id)


async def test_list_requires_active_viewer_session(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)

    with pytest.raises(ViewerNotPresentError):
        await list_profiles(db_session, venue_id, viewer_id)


async def test_list_raises_for_unknown_venue(db_session):
    with pytest.raises(VenueNotFoundError):
        await list_profiles(db_session, "no-such-venue", "any-user")


async def test_pagination_returns_next_cursor(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    waited_ids = [
        await create_session(db_session, await create_user(db_session), venue_id)
        for _ in range(3)
    ]

    first_items, first_cursor = await list_profiles(
        db_session, venue_id, viewer_id, limit=2
    )
    assert len(first_items) == 2
    assert first_cursor is not None

    second_items, second_cursor = await list_profiles(
        db_session, venue_id, viewer_id, limit=2, cursor=first_cursor
    )
    assert len(second_items) == 1
    assert second_cursor is None
    assert {p.presenceId for p in first_items} | {p.presenceId for p in second_items} == set(
        waited_ids
    )


async def test_get_profile_returns_full_profile(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    other_id = await create_user(db_session, bio="Hi!")
    presence_id = await create_session(db_session, other_id, venue_id)
    await create_photo(db_session, other_id, position=0)

    profile = await get_profile(db_session, presence_id, viewer_id)

    assert profile.userId == other_id
    assert profile.presenceId == presence_id
    assert profile.venueId == venue_id
    assert profile.bio == "Hi!"
    assert profile.displayName.startswith("user-")


async def test_get_profile_hides_other_venues(db_session):
    venue_id = await create_venue(db_session)
    other_venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    other_id = await create_user(db_session)
    presence_id = await create_session(db_session, other_id, other_venue_id)

    with pytest.raises(ProfileNotFoundError):
        await get_profile(db_session, presence_id, viewer_id)


async def test_get_profile_requires_viewer_presence(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    other_id = await create_user(db_session)
    presence_id = await create_session(db_session, other_id, venue_id)

    with pytest.raises(ViewerNotPresentError):
        await get_profile(db_session, presence_id, viewer_id)


async def test_chat_only_mode_excludes_ask_to_approach(db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    other_id = await create_user(db_session)
    await create_session(
        db_session, other_id, venue_id, approach_mode=ApproachMode.CHAT_ONLY
    )

    items, _ = await list_profiles(db_session, venue_id, viewer_id)

    assert items[0].availableActions == ["contact"]