"""API tests for profile photo upload/delete and media serving."""

from fastapi.testclient import TestClient

from tests.conftest import create_user

PNG_CONTENT = b"\x89PNG\r\n\x1a\n" + b"0" * 200


def auth_headers(user_id: str) -> dict[str, str]:
    return {"X-Dev-User-Id": user_id}


async def test_upload_photo_returns_public_url(client: TestClient, db_session):
    user_id = await create_user(db_session)

    response = client.post(
        "/me/profile/photos",
        headers=auth_headers(user_id),
        files={"file": ("face.png", PNG_CONTENT, "image/png")},
    )

    assert response.status_code == 200
    photo = response.json()["data"]["photos"][0]
    assert photo["position"] == 1
    assert photo["moderationStatus"] == "approved"
    assert photo["url"].startswith("http://localhost:8000/media/")


async def test_upload_requires_auth(client: TestClient):
    response = client.post(
        "/me/profile/photos", files={"file": ("face.png", PNG_CONTENT, "image/png")}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_upload_rejects_non_image(client: TestClient, db_session):
    user_id = await create_user(db_session)

    response = client.post(
        "/me/profile/photos",
        headers=auth_headers(user_id),
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_media_serves_uploaded_bytes(client: TestClient, db_session):
    user_id = await create_user(db_session)
    uploaded = client.post(
        "/me/profile/photos",
        headers=auth_headers(user_id),
        files={"file": ("face.png", PNG_CONTENT, "image/png")},
    ).json()["data"]["photos"][0]
    photo_id = uploaded["url"].rsplit("/", 1)[-1]

    response = client.get(f"/media/{photo_id}")

    assert response.status_code == 200
    assert response.content == PNG_CONTENT
    assert response.headers["content-type"].startswith("image/png")


async def test_delete_photo_removes_from_profile(client: TestClient, db_session):
    user_id = await create_user(db_session)
    uploaded = client.post(
        "/me/profile/photos",
        headers=auth_headers(user_id),
        files={"file": ("face.png", PNG_CONTENT, "image/png")},
    ).json()["data"]
    photo_id = uploaded["photos"][0]["id"]

    response = client.delete(
        f"/me/profile/photos/{photo_id}", headers=auth_headers(user_id)
    )

    assert response.status_code == 200
    assert response.json()["data"]["photos"] == []
    gone = client.get(f"/media/{photo_id}")
    assert gone.status_code == 404


async def test_delete_foreign_photo_returns_404(client: TestClient, db_session):
    owner_id = await create_user(db_session)
    stranger_id = await create_user(db_session)
    photo_id = client.post(
        "/me/profile/photos",
        headers=auth_headers(owner_id),
        files={"file": ("face.png", PNG_CONTENT, "image/png")},
    ).json()["data"]["photos"][0]["id"]

    response = client.delete(
        f"/me/profile/photos/{photo_id}", headers=auth_headers(stranger_id)
    )

    assert response.status_code == 404


async def test_media_returns_404_for_unknown_photo(client: TestClient):
    response = client.get("/media/no-such-photo")

    assert response.status_code == 404