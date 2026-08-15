"""API tests for the drink offer endpoints."""

from tests.conftest import (
    block_users,
    create_menu_item,
    create_session,
    create_user,
    create_venue,
)


def headers(user_id: str) -> dict[str, str]:
    return {"X-Dev-User-Id": user_id}


async def test_menu_endpoint_lists_available_items(client, db_session):
    venue_id = await create_venue(db_session)
    item_id = await create_menu_item(db_session, venue_id, name="Negroni", price_minor=350)
    response = client.get(f"/venues/{venue_id}/menu")
    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "id": item_id,
                "venueId": venue_id,
                "name": "Negroni",
                "description": None,
                "price": {"amountMinor": 350, "currency": "RUB"},
                "imageUrl": None,
                "availabilityStatus": "available",
            }
        ]
    }


async def test_menu_endpoint_404_for_unknown_venue(client):
    response = client.get("/venues/no-such-venue/menu")
    assert response.status_code == 404


async def test_send_offer_endpoint_creates_offer(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)

    response = client.post(
        "/me/drink-offers",
        headers=headers(sender_id),
        json={
            "recipientPresenceId": recipient_presence,
            "menuItemId": item_id,
            "idempotencyKey": "key-1",
        },
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["senderUserId"] == sender_id
    assert body["recipientUserId"] == recipient_id
    assert body["status"] == "payment_authorized"
    assert body["itemNameSnapshot"] == "Negroni"
    assert body["priceSnapshot"] == {"amountMinor": 350, "currency": "RUB"}
    assert body["expiresAt"] is not None


async def test_send_offer_replay_returns_same_offer(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    payload = {
        "recipientPresenceId": recipient_presence,
        "menuItemId": item_id,
        "idempotencyKey": "key-1",
    }
    first = client.post("/me/drink-offers", headers=headers(sender_id), json=payload)
    second = client.post("/me/drink-offers", headers=headers(sender_id), json=payload)
    assert first.status_code == 201 and second.status_code == 201
    assert first.json()["data"]["id"] == second.json()["data"]["id"]


async def test_send_offer_requires_presence(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    response = client.post(
        "/me/drink-offers",
        headers=headers(sender_id),
        json={
            "recipientPresenceId": recipient_presence,
            "menuItemId": item_id,
            "idempotencyKey": "key-1",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ACTIVE_PRESENCE_REQUIRED"


async def test_send_offer_forbidden_without_verification(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session, verified=False)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    response = client.post(
        "/me/drink-offers",
        headers=headers(sender_id),
        json={
            "recipientPresenceId": recipient_presence,
            "menuItemId": item_id,
            "idempotencyKey": "key-1",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_send_offer_rejects_blocked_recipient(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    await block_users(db_session, recipient_id, sender_id)
    response = client.post(
        "/me/drink-offers",
        headers=headers(sender_id),
        json={
            "recipientPresenceId": recipient_presence,
            "menuItemId": item_id,
            "idempotencyKey": "key-1",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_send_offer_rejects_unavailable_item(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id, availability="unavailable")
    response = client.post(
        "/me/drink-offers",
        headers=headers(sender_id),
        json={
            "recipientPresenceId": recipient_presence,
            "menuItemId": item_id,
            "idempotencyKey": "key-1",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MENU_ITEM_UNAVAILABLE"


async def test_accept_and_redeem_flow(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)

    send_response = client.post(
        "/me/drink-offers",
        headers=headers(sender_id),
        json={
            "recipientPresenceId": recipient_presence,
            "menuItemId": item_id,
            "idempotencyKey": "key-1",
        },
    )
    offer_id = send_response.json()["data"]["id"]

    accept_response = client.post(
        f"/me/drink-offers/{offer_id}/response",
        headers=headers(recipient_id),
        json={"decision": "accept"},
    )
    assert accept_response.status_code == 200
    accept_body = accept_response.json()["data"]
    assert accept_body["offer"]["status"] == "accepted"
    code = accept_body["redemption"]["code"]
    assert code.isdigit() and len(code) == 6

    redeem_response = client.post(
        "/me/redemptions",
        headers=headers(recipient_id),
        json={"redemptionCode": code, "idempotencyKey": "key-1"},
    )
    assert redeem_response.status_code == 200
    assert redeem_response.json()["data"]["status"] == "redeemed"

    replay = client.post(
        "/me/redemptions",
        headers=headers(recipient_id),
        json={"redemptionCode": code, "idempotencyKey": "key-2"},
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["status"] == "redeemed"


async def test_decline_voids_offer(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    offer_id = client.post(
        "/me/drink-offers",
        headers=headers(sender_id),
        json={
            "recipientPresenceId": recipient_presence,
            "menuItemId": item_id,
            "idempotencyKey": "key-1",
        },
    ).json()["data"]["id"]

    response = client.post(
        f"/me/drink-offers/{offer_id}/response",
        headers=headers(recipient_id),
        json={"decision": "decline"},
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["offer"]["status"] == "declined"
    assert body["redemption"] is None


async def test_respond_forbidden_for_sender(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    offer_id = client.post(
        "/me/drink-offers",
        headers=headers(sender_id),
        json={
            "recipientPresenceId": recipient_presence,
            "menuItemId": item_id,
            "idempotencyKey": "key-1",
        },
    ).json()["data"]["id"]

    response = client.post(
        f"/me/drink-offers/{offer_id}/response",
        headers=headers(sender_id),
        json={"decision": "accept"},
    )
    assert response.status_code == 404


async def test_redeem_rejects_unknown_code(client, db_session):
    response = client.post(
        "/me/redemptions",
        headers=headers("any-user"),
        json={"redemptionCode": "000000", "idempotencyKey": "key-1"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_my_offers_endpoint_returns_statuses(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    offer_id = client.post(
        "/me/drink-offers",
        headers=headers(sender_id),
        json={
            "recipientPresenceId": recipient_presence,
            "menuItemId": item_id,
            "idempotencyKey": "key-1",
        },
    ).json()["data"]["id"]
    client.post(
        f"/me/drink-offers/{offer_id}/response",
        headers=headers(recipient_id),
        json={"decision": "decline"},
    )

    sender_list = client.get("/me/drink-offers", headers=headers(sender_id))
    assert sender_list.status_code == 200
    assert sender_list.json() == {
        "data": [
            {
                "id": offer_id,
                "senderUserId": sender_id,
                "recipientUserId": recipient_id,
                "senderPresenceId": sender_list.json()["data"][0]["senderPresenceId"],
                "recipientPresenceId": recipient_presence,
                "venueId": venue_id,
                "menuItemId": item_id,
                "connectionId": None,
                "status": "declined",
                "itemNameSnapshot": "Negroni",
                "priceSnapshot": {"amountMinor": 350, "currency": "RUB"},
                "createdAt": sender_list.json()["data"][0]["createdAt"],
                "respondedAt": sender_list.json()["data"][0]["respondedAt"],
                "expiresAt": sender_list.json()["data"][0]["expiresAt"],
            }
        ]
    }

    recipient_list = client.get("/me/drink-offers", headers=headers(recipient_id))
    assert recipient_list.status_code == 200
    assert [item["status"] for item in recipient_list.json()["data"]] == ["declined"]

    stranger_list = client.get(
        "/me/drink-offers", headers=headers(await create_user(db_session))
    )
    assert stranger_list.json() == {"data": []}
