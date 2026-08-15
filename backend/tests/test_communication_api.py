"""API tests for contact requests and the messenger."""

from tests.conftest import (
    block_users,
    create_connection_with_chat,
    create_session,
    create_user,
    create_venue,
)


def headers(user_id: str) -> dict[str, str]:
    return {"X-Dev-User-Id": user_id}


async def seed_pair(client, db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    return venue_id, sender_id, recipient_id, recipient_presence


async def test_full_chat_flow(client, db_session):
    _, sender_id, recipient_id, recipient_presence = await seed_pair(client, db_session)

    send = client.post(
        "/me/contact-requests",
        headers=headers(sender_id),
        json={"recipientPresenceId": recipient_presence, "message": "hi!"},
    )
    assert send.status_code == 201
    request_id = send.json()["data"]["id"]
    assert send.json()["data"]["status"] == "pending"

    duplicate = client.post(
        "/me/contact-requests",
        headers=headers(sender_id),
        json={"recipientPresenceId": recipient_presence},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "REQUEST_ALREADY_EXISTS"

    incoming = client.get("/me/contact-requests", headers=headers(recipient_id))
    assert [item["id"] for item in incoming.json()["data"]] == [request_id]

    accept = client.post(
        f"/me/contact-requests/{request_id}/response",
        headers=headers(recipient_id),
        json={"decision": "accept"},
    )
    assert accept.status_code == 200
    assert accept.json()["data"]["status"] == "accepted"

    conversations = client.get("/me/conversations", headers=headers(sender_id))
    assert conversations.status_code == 200
    conversation_id = conversations.json()["data"][0]["id"]
    assert conversations.json()["data"][0]["peerUserId"] == recipient_id

    message = client.post(
        f"/me/conversations/{conversation_id}/messages",
        headers=headers(sender_id),
        json={"body": "привет!"},
    )
    assert message.status_code == 201
    assert message.json()["data"]["senderUserId"] == sender_id

    history = client.get(
        f"/me/conversations/{conversation_id}/messages", headers=headers(recipient_id)
    )
    assert history.status_code == 200
    assert [item["body"] for item in history.json()["data"]["items"]] == ["привет!"]

    unread = client.get("/me/conversations", headers=headers(recipient_id))
    assert unread.json()["data"][0]["unreadCount"] == 1


async def test_decline_then_status_visible(client, db_session):
    _, sender_id, recipient_id, recipient_presence = await seed_pair(client, db_session)
    request_id = client.post(
        "/me/contact-requests",
        headers=headers(sender_id),
        json={"recipientPresenceId": recipient_presence},
    ).json()["data"]["id"]

    decline = client.post(
        f"/me/contact-requests/{request_id}/response",
        headers=headers(recipient_id),
        json={"decision": "decline"},
    )
    assert decline.json()["data"]["status"] == "declined"

    sender_list = client.get("/me/contact-requests", headers=headers(sender_id))
    assert [item["status"] for item in sender_list.json()["data"]] == ["declined"]
    assert client.get("/me/conversations", headers=headers(sender_id)).json()["data"] == []


async def test_send_request_forbidden_when_blocked(client, db_session):
    _, sender_id, recipient_id, recipient_presence = await seed_pair(client, db_session)
    await block_users(db_session, sender_id, recipient_id)
    response = client.post(
        "/me/contact-requests",
        headers=headers(sender_id),
        json={"recipientPresenceId": recipient_presence},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_response_requires_recipient(client, db_session):
    _, sender_id, _recipient_id, recipient_presence = await seed_pair(client, db_session)
    request_id = client.post(
        "/me/contact-requests",
        headers=headers(sender_id),
        json={"recipientPresenceId": recipient_presence},
    ).json()["data"]["id"]

    response = client.post(
        f"/me/contact-requests/{request_id}/response",
        headers=headers(sender_id),
        json={"decision": "accept"},
    )
    assert response.status_code == 404


async def test_send_message_forbidden_for_stranger(client, db_session):
    venue_id = await create_venue(db_session)
    user_a = await create_user(db_session)
    user_b = await create_user(db_session)
    stranger = await create_user(db_session)
    _, conversation_id = await create_connection_with_chat(db_session, user_a, user_b, venue_id)

    response = client.post(
        f"/me/conversations/{conversation_id}/messages",
        headers=headers(stranger),
        json={"body": "intrude"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"

    history = client.get(
        f"/me/conversations/{conversation_id}/messages", headers=headers(stranger)
    )
    assert history.status_code == 404


async def test_empty_state(client, db_session):
    user_id = await create_user(db_session)
    assert client.get("/me/conversations", headers=headers(user_id)).json() == {"data": []}
    assert client.get("/me/contact-requests", headers=headers(user_id)).json() == {
        "data": []
    }
