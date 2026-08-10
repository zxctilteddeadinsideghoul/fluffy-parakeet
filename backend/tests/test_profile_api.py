"""API tests for GET/PUT /me/profile."""

from fastapi.testclient import TestClient

from tests.conftest import create_user


def auth_headers(user_id: str) -> dict[str, str]:
    return {"X-Dev-User-Id": user_id}


async def test_get_me_profile_requires_auth(client: TestClient):
    response = client.get("/me/profile")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_get_me_profile_returns_empty_profile_for_fresh_user(
    client: TestClient, db_session
):
    user_id = await create_user(db_session, verified=False, display_name="Solo")

    response = client.get("/me/profile", headers=auth_headers(user_id))

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["id"] == user_id
    assert body["age"] == 26
    assert body["verification"] == {"isVerified": False}
    assert body["photos"] == []


async def test_put_me_profile_updates_fields(client: TestClient, db_session):
    user_id = await create_user(db_session)

    response = client.put(
        "/me/profile",
        headers=auth_headers(user_id),
        json={
            "displayName": "Alice",
            "gender": "female",
            "bio": "Hi there!",
            "birthDate": "1991-05-20",
            "communicationGoals": ["dating", "friends"],
            "defaultApproachMode": "may_approach",
            "visibilityEnabled": True,
        },
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["displayName"] == "Alice"
    assert body["gender"] == "female"
    assert body["bio"] == "Hi there!"
    assert body["communicationGoals"] == ["dating", "friends"]
    assert body["defaultApproachMode"] == "may_approach"
    assert body["age"] == 35

    reloaded = client.get("/me/profile", headers=auth_headers(user_id)).json()["data"]
    assert reloaded["displayName"] == "Alice"
    assert reloaded["communicationGoals"] == ["dating", "friends"]


async def test_put_me_profile_rejects_visible_profile_without_name(
    client: TestClient, db_session
):
    user_id = await create_user(db_session)

    response = client.put(
        "/me/profile",
        headers=auth_headers(user_id),
        json={
            "displayName": "  ",
            "communicationGoals": [],
            "defaultApproachMode": "chat_only",
            "visibilityEnabled": True,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_put_me_profile_rejects_unknown_goal(client: TestClient, db_session):
    user_id = await create_user(db_session)

    response = client.put(
        "/me/profile",
        headers=auth_headers(user_id),
        json={
            "displayName": "Alice",
            "communicationGoals": ["not-a-goal"],
            "defaultApproachMode": "chat_only",
            "visibilityEnabled": False,
        },
    )

    assert response.status_code == 422


async def test_put_me_profile_returns_404_for_unknown_user(client: TestClient):
    response = client.put(
        "/me/profile",
        headers=auth_headers("no-such-user"),
        json={
            "displayName": "Ghost",
            "communicationGoals": [],
            "defaultApproachMode": "chat_only",
            "visibilityEnabled": True,
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"