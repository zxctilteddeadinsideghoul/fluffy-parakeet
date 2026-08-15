"""Use case tests for contact requests, connections and the messenger."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.enums import ConversationStatus, RequestStatus
from app.repositories.communication import CommunicationRepository
from app.schemas.communication import (
    SendContactRequestRequest,
    SendMessageRequest,
)
from app.use_cases.list_conversations import ListConversationsUseCase
from app.use_cases.list_messages import ListMessagesUseCase
from app.use_cases.list_my_contact_requests import ListMyContactRequestsUseCase
from app.use_cases.respond_to_contact_request import (
    RequestExpiredError,
    RequestNotFoundError,
    RespondToContactRequestUseCase,
)
from app.use_cases.send_contact_request import (
    BlockedError,
    NoActivePresenceError,
    NotSameVenueError,
    RequestAlreadyExistsError,
    SelfInteractionError,
    SendContactRequestUseCase,
)
from app.use_cases.send_message import (
    ConversationNotFoundError,
    InvalidStateTransitionError,
    NotMemberError,
    SendMessageUseCase,
)
from tests.conftest import (
    block_users,
    create_connection_with_chat,
    create_session,
    create_user,
    create_venue,
)


def repo(session) -> CommunicationRepository:
    return CommunicationRepository(session)


async def build_present_pair(session):
    venue_id = await create_venue(session)
    sender_id = await create_user(session)
    recipient_id = await create_user(session)
    await create_session(session, sender_id, venue_id)
    recipient_presence = await create_session(session, recipient_id, venue_id)
    return venue_id, sender_id, recipient_id, recipient_presence


async def test_send_creates_pending_request(db_session):
    venue_id, sender_id, recipient_id, recipient_presence = await build_present_pair(db_session)
    use_case = SendContactRequestUseCase(db_session, repo(db_session))
    request = await use_case.execute(
        user_id=sender_id,
        command=SendContactRequestRequest(
            recipientPresenceId=recipient_presence, message="hi"
        ),
    )
    assert request.status == RequestStatus.PENDING
    assert request.sender_user_id == sender_id
    assert request.recipient_user_id == recipient_id
    assert request.venue_id == venue_id
    assert request.message == "hi"
    assert request.expires_at is not None


async def test_send_requires_active_sender_presence(db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    use_case = SendContactRequestUseCase(db_session, repo(db_session))
    with pytest.raises(NoActivePresenceError):
        await use_case.execute(
            user_id=sender_id,
            command=SendContactRequestRequest(recipientPresenceId=recipient_presence),
        )


async def test_send_rejects_self_interaction(db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    own_presence = await create_session(db_session, sender_id, venue_id)
    use_case = SendContactRequestUseCase(db_session, repo(db_session))
    with pytest.raises(SelfInteractionError):
        await use_case.execute(
            user_id=sender_id,
            command=SendContactRequestRequest(recipientPresenceId=own_presence),
        )


async def test_send_rejects_duplicate_request(db_session):
    _, sender_id, _, recipient_presence = await build_present_pair(db_session)
    use_case = SendContactRequestUseCase(db_session, repo(db_session))
    await use_case.execute(
        user_id=sender_id,
        command=SendContactRequestRequest(recipientPresenceId=recipient_presence),
    )
    with pytest.raises(RequestAlreadyExistsError):
        await use_case.execute(
            user_id=sender_id,
            command=SendContactRequestRequest(recipientPresenceId=recipient_presence),
        )


async def test_send_rejects_blocked_recipient(db_session):
    _, sender_id, recipient_id, recipient_presence = await build_present_pair(db_session)
    await block_users(db_session, sender_id, recipient_id)
    use_case = SendContactRequestUseCase(db_session, repo(db_session))
    with pytest.raises(BlockedError):
        await use_case.execute(
            user_id=sender_id,
            command=SendContactRequestRequest(recipientPresenceId=recipient_presence),
        )


async def test_send_rejects_recipient_in_other_venue(db_session):
    _, sender_id, _, _ = await build_present_pair(db_session)
    other_venue_id = await create_venue(db_session)
    other_user_id = await create_user(db_session)
    other_presence = await create_session(db_session, other_user_id, other_venue_id)
    use_case = SendContactRequestUseCase(db_session, repo(db_session))
    with pytest.raises(NotSameVenueError):
        await use_case.execute(
            user_id=sender_id,
            command=SendContactRequestRequest(recipientPresenceId=other_presence),
        )


async def test_accept_creates_connection_conversation_and_members(db_session):
    _venue_id, sender_id, recipient_id, recipient_presence = await build_present_pair(db_session)
    send = SendContactRequestUseCase(db_session, repo(db_session))
    request = await send.execute(
        user_id=sender_id,
        command=SendContactRequestRequest(recipientPresenceId=recipient_presence),
    )
    use_case = RespondToContactRequestUseCase(db_session, repo(db_session))
    updated = await use_case.execute(user_id=recipient_id, request_id=request.id, decision="accept")
    assert updated.status == RequestStatus.ACCEPTED
    assert updated.responded_at is not None

    from app.models.communication import ConnectionOrm, ConversationMemberOrm, ConversationOrm

    connection = (
        await db_session.execute(
            select(ConnectionOrm).where(ConnectionOrm.source_request_id == request.id)
        )
    ).scalar_one()
    conversation = (
        await db_session.execute(
            select(ConversationOrm).where(ConversationOrm.connection_id == connection.id)
        )
    ).scalar_one()
    members = (
        await db_session.execute(
            select(ConversationMemberOrm).where(
                ConversationMemberOrm.conversation_id == conversation.id
            )
        )
    ).scalars().all()
    assert {member.user_id for member in members} == {sender_id, recipient_id}


async def test_decline_marks_request(db_session):
    _, sender_id, recipient_id, recipient_presence = await build_present_pair(db_session)
    send = SendContactRequestUseCase(db_session, repo(db_session))
    request = await send.execute(
        user_id=sender_id,
        command=SendContactRequestRequest(recipientPresenceId=recipient_presence),
    )
    use_case = RespondToContactRequestUseCase(db_session, repo(db_session))
    updated = await use_case.execute(user_id=recipient_id, request_id=request.id, decision="decline")
    assert updated.status == RequestStatus.DECLINED


async def test_respond_hides_foreign_requests(db_session):
    _, sender_id, _recipient_id, recipient_presence = await build_present_pair(db_session)
    send = SendContactRequestUseCase(db_session, repo(db_session))
    request = await send.execute(
        user_id=sender_id,
        command=SendContactRequestRequest(recipientPresenceId=recipient_presence),
    )
    use_case = RespondToContactRequestUseCase(db_session, repo(db_session))
    with pytest.raises(RequestNotFoundError):
        await use_case.execute(user_id=sender_id, request_id=request.id, decision="accept")


async def test_respond_twice_is_rejected(db_session):
    _, sender_id, recipient_id, recipient_presence = await build_present_pair(db_session)
    send = SendContactRequestUseCase(db_session, repo(db_session))
    request = await send.execute(
        user_id=sender_id,
        command=SendContactRequestRequest(recipientPresenceId=recipient_presence),
    )
    use_case = RespondToContactRequestUseCase(db_session, repo(db_session))
    await use_case.execute(user_id=recipient_id, request_id=request.id, decision="accept")
    with pytest.raises(Exception) as exc_info:
        await use_case.execute(user_id=recipient_id, request_id=request.id, decision="decline")
    assert type(exc_info.value).__name__ == "InvalidStateTransitionError"


async def test_expired_request_cannot_be_responded(db_session):
    _, sender_id, recipient_id, recipient_presence = await build_present_pair(db_session)
    send = SendContactRequestUseCase(db_session, repo(db_session))
    request = await send.execute(
        user_id=sender_id,
        command=SendContactRequestRequest(recipientPresenceId=recipient_presence),
    )
    request.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)
    await db_session.flush()
    use_case = RespondToContactRequestUseCase(db_session, repo(db_session))
    with pytest.raises(RequestExpiredError):
        await use_case.execute(user_id=recipient_id, request_id=request.id, decision="accept")
    refreshed = await repo(db_session).get_request(request.id)
    assert refreshed.status == RequestStatus.EXPIRED


async def test_list_requests_returns_my_requests(db_session):
    _, sender_id, recipient_id, recipient_presence = await build_present_pair(db_session)
    send = SendContactRequestUseCase(db_session, repo(db_session))
    await send.execute(
        user_id=sender_id,
        command=SendContactRequestRequest(recipientPresenceId=recipient_presence),
    )
    use_case = ListMyContactRequestsUseCase(repo(db_session))
    sender_items = await use_case.execute(user_id=sender_id)
    recipient_items = await use_case.execute(user_id=recipient_id)
    assert len(sender_items) == 1
    assert sender_items[0].status == "pending"
    assert recipient_items[0].recipient_user_id == recipient_id


async def test_conversations_show_peer_and_last_message(db_session):
    venue_id = await create_venue(db_session)
    user_a = await create_user(db_session)
    user_b = await create_user(db_session)
    _, conversation_id = await create_connection_with_chat(db_session, user_a, user_b, venue_id)
    await SendMessageUseCase(db_session, repo(db_session)).execute(
        user_id=user_a,
        conversation_id=conversation_id,
        command=SendMessageRequest(body="hello"),
    )
    items = await ListConversationsUseCase(repo(db_session)).execute(user_id=user_b)
    assert len(items) == 1
    assert items[0].peer_user_id == user_a
    assert items[0].last_message_body == "hello"
    assert items[0].last_message_at is not None


async def test_unread_count_ignores_own_messages(db_session):
    venue_id = await create_venue(db_session)
    user_a = await create_user(db_session)
    user_b = await create_user(db_session)
    _, conversation_id = await create_connection_with_chat(db_session, user_a, user_b, venue_id)
    send = SendMessageUseCase(db_session, repo(db_session))
    await send.execute(
        user_id=user_a, conversation_id=conversation_id, command=SendMessageRequest(body="a1")
    )
    await send.execute(
        user_id=user_a, conversation_id=conversation_id, command=SendMessageRequest(body="a2")
    )
    await send.execute(
        user_id=user_b, conversation_id=conversation_id, command=SendMessageRequest(body="b1")
    )
    items = await ListConversationsUseCase(repo(db_session)).execute(user_id=user_b)
    assert items[0].unread_count == 2


async def test_send_message_requires_membership(db_session):
    venue_id = await create_venue(db_session)
    user_a = await create_user(db_session)
    user_b = await create_user(db_session)
    stranger = await create_user(db_session)
    _, conversation_id = await create_connection_with_chat(db_session, user_a, user_b, venue_id)
    use_case = SendMessageUseCase(db_session, repo(db_session))
    with pytest.raises(NotMemberError):
        await use_case.execute(
            user_id=stranger,
            conversation_id=conversation_id,
            command=SendMessageRequest(body="intrude"),
        )
    with pytest.raises(ConversationNotFoundError):
        await use_case.execute(
            user_id=user_a,
            conversation_id="no-such-chat",
            command=SendMessageRequest(body="nowhere"),
        )


async def test_send_message_rejects_inactive_conversation(db_session):
    venue_id = await create_venue(db_session)
    user_a = await create_user(db_session)
    user_b = await create_user(db_session)
    _, conversation_id = await create_connection_with_chat(db_session, user_a, user_b, venue_id)
    from app.models.communication import ConversationOrm

    conversation = await db_session.get(ConversationOrm, conversation_id)
    conversation.status = ConversationStatus.CLOSED
    await db_session.flush()
    use_case = SendMessageUseCase(db_session, repo(db_session))
    with pytest.raises(InvalidStateTransitionError):
        await use_case.execute(
            user_id=user_a,
            conversation_id=conversation_id,
            command=SendMessageRequest(body="too late"),
        )


async def test_messages_paginate(db_session):
    venue_id = await create_venue(db_session)
    user_a = await create_user(db_session)
    user_b = await create_user(db_session)
    _, conversation_id = await create_connection_with_chat(db_session, user_a, user_b, venue_id)
    send = SendMessageUseCase(db_session, repo(db_session))
    for i in range(5):
        await send.execute(
            user_id=user_a,
            conversation_id=conversation_id,
            command=SendMessageRequest(body=f"msg-{i}"),
        )
    use_case = ListMessagesUseCase(repo(db_session))
    page1 = await use_case.execute(
        user_id=user_a, conversation_id=conversation_id, limit=2, cursor=None
    )
    assert [m.body for m in page1.items] == ["msg-0", "msg-1"]
    assert page1.next_cursor is not None
    page2 = await use_case.execute(
        user_id=user_a, conversation_id=conversation_id, limit=2, cursor=page1.next_cursor
    )
    assert [m.body for m in page2.items] == ["msg-2", "msg-3"]
    assert page2.next_cursor is not None


async def test_messages_hidden_for_non_members(db_session):
    venue_id = await create_venue(db_session)
    user_a = await create_user(db_session)
    user_b = await create_user(db_session)
    stranger = await create_user(db_session)
    _, conversation_id = await create_connection_with_chat(db_session, user_a, user_b, venue_id)
    use_case = ListMessagesUseCase(repo(db_session))
    with pytest.raises(Exception) as exc_info:
        await use_case.execute(
            user_id=stranger, conversation_id=conversation_id, limit=20, cursor=None
        )
    assert type(exc_info.value).__name__ == "ConversationNotFoundError"
