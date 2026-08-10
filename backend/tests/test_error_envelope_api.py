"""Tests for the unified HTTP error envelope (contract section 7)."""

from tests.conftest import create_session, create_user, create_venue


def headers(user_id: str) -> dict[str, str]:
    return {"X-Dev-User-Id": user_id}


async def test_401_uses_contract_envelope(client):
    response = client.get("/venues/00000000-0000-0000-0000-000000000000/profiles")

    assert response.status_code == 401
    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert error["code"] == "AUTH_REQUIRED"
    assert error["message"]
    assert len(error["traceId"]) == 16
    assert "details" not in error


async def test_409_uses_contract_code(client, db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)

    response = client.get(
        f"/venues/{venue_id}/profiles",
        headers=headers(viewer_id),
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "ACTIVE_PRESENCE_REQUIRED"
    assert body["error"]["message"]
    assert body["error"]["traceId"]


async def test_404_uses_contract_code(client, db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)
    other_id = await create_user(db_session)
    await create_session(db_session, viewer_id, venue_id)
    await create_session(db_session, other_id, venue_id)

    response = client.get(
        "/presence/00000000-0000-0000-0000-000000000000/profile",
        headers=headers(viewer_id),
    )

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"]
    assert body["error"]["traceId"]


async def test_unknown_route_uses_contract_envelope(client):
    response = client.get("/no-such-route")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["traceId"]


async def test_validation_error_is_lean_envelope(client, db_session):
    await create_venue(db_session)
    viewer_id = await create_user(db_session)

    response = client.post(
        "/presence/check-in",
        json={"venueToken": 123},
        headers=headers(viewer_id),
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "details" not in error


async def test_trace_id_is_exposed_as_header(client, db_session):
    venue_id = await create_venue(db_session)
    viewer_id = await create_user(db_session)

    response = client.get(
        f"/venues/{venue_id}/profiles",
        headers=headers(viewer_id),
    )

    assert response.status_code == 409
    trace_id = response.headers["X-Trace-Id"]
    assert trace_id == response.json()["error"]["traceId"]