"""API tests for presence check-in and check-out."""

from tests.conftest import create_token, create_user, create_venue


def headers(user_id: str) -> dict[str, str]:
    return {"X-Dev-User-Id": user_id}


def test_check_in_requires_auth(client):
    response = client.post(
        "/presence/check-in",
        json={"venueToken": "t", "visibility": "visible", "approachMode": "chat_only"},
    )

    assert response.status_code == 401


def test_check_in_returns_created_session(client, db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)

    response = client.post(
        "/presence/check-in",
        headers=headers(user_id),
        json={"venueToken": "secret-token", "visibility": "visible", "approachMode": "chat_only"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["venueId"] == venue_id
    assert body["status"] == "active"
    assert body["visibility"] == "visible"
    assert body["approachMode"] == "chat_only"
    assert body["id"]
    assert body["expiresAt"]


def test_check_in_rejects_bad_token(client, db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)

    response = client.post(
        "/presence/check-in",
        headers=headers(user_id),
        json={"venueToken": "nope", "visibility": "visible", "approachMode": "chat_only"},
    )

    assert response.status_code == 404


def test_check_in_rejects_second_session(client, db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    payload = {"venueToken": "secret-token", "visibility": "visible", "approachMode": "chat_only"}

    first = client.post("/presence/check-in", headers=headers(user_id), json=payload)
    second = client.post("/presence/check-in", headers=headers(user_id), json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_check_out_requires_auth(client):
    response = client.post("/presence/check-out")

    assert response.status_code == 401


def test_check_out_ends_session(client, db_session):
    venue_id = create_venue(db_session)
    user_id = create_user(db_session)
    create_token(db_session, venue_id)
    client.post(
        "/presence/check-in",
        headers=headers(user_id),
        json={"venueToken": "secret-token", "visibility": "visible", "approachMode": "chat_only"},
    )

    response = client.post("/presence/check-out", headers=headers(user_id))

    assert response.status_code == 200
    assert response.json()["status"] == "ended"


def test_check_out_without_session_returns_404(client, db_session):
    user_id = create_user(db_session)

    response = client.post("/presence/check-out", headers=headers(user_id))

    assert response.status_code == 404
