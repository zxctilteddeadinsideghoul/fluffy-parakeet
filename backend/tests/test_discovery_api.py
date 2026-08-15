"""API tests for the present-profiles discovery endpoints."""

from tests.conftest import create_photo, create_session, create_user, create_venue


def headers(user_id: str) -> dict[str, str]:
    return {"X-Dev-User-Id": user_id}


async def test_list_profiles_requires_auth(client):
    response = client.get("/venues/any-venue/profiles")

    assert response.status_code == 401


async def test_list_profiles_returns_page(client, db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    other_id = await create_user(db_session, display_name="Anna")
    await create_session(db_session, other_id, venue_id)
    await create_photo(db_session, other_id)

    response = client.get(f"/venues/{venue_id}/profiles", headers=headers(viewer_id))

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["nextCursor"] is None
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["userId"] == other_id
    assert item["displayName"] == "Anna"
    assert item["age"] == 26
    assert item["isVerified"] is True
    assert item["photos"][0]["url"]
    assert item["availableActions"] == ["contact", "drink", "ask_to_approach"]


async def test_list_profiles_without_viewer_presence_returns_409(client, db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)

    response = client.get(f"/venues/{venue_id}/profiles", headers=headers(viewer_id))

    assert response.status_code == 409


async def test_list_profiles_unknown_venue_returns_404(client, db_session):
    viewer_id = await create_user(db_session)

    response = client.get("/venues/unknown-venue/profiles", headers=headers(viewer_id))

    assert response.status_code == 404


async def test_get_profile_returns_full_profile(client, db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    other_id = await create_user(db_session, bio="Hi there!")
    presence_id = await create_session(db_session, other_id, venue_id)

    response = client.get(
        f"/presence/{presence_id}/profile", headers=headers(viewer_id)
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["presenceId"] == presence_id
    assert body["userId"] == other_id
    assert body["bio"] == "Hi there!"


async def test_get_profile_of_other_venue_returns_404(client, db_session):
    venue_id = await create_venue(db_session)
    other_venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    other_id = await create_user(db_session)
    presence_id = await create_session(db_session, other_id, other_venue_id)

    response = client.get(
        f"/presence/{presence_id}/profile", headers=headers(viewer_id)
    )

    assert response.status_code == 404


async def test_get_profile_requires_auth(client):
    response = client.get("/presence/unknown/profile")

    assert response.status_code == 401


async def test_get_profile_without_viewer_presence_returns_409(client, db_session):
    viewer_id = await create_user(db_session)
    venue_id = await create_venue(db_session)
    other_id = await create_user(db_session)
    presence_id = await create_session(db_session, other_id, venue_id)

    response = client.get(
        f"/presence/{presence_id}/profile", headers=headers(viewer_id)
    )

    assert response.status_code == 409