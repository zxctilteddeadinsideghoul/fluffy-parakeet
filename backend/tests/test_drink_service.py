"""Use case tests for the drink offer flow (send, respond, redeem, menu)."""

from datetime import timedelta

import pytest

from app.models.drink import DrinkOfferOrm, PaymentOrm
from app.models.enums import (
    DrinkOfferStatus,
    PaymentStatus,
    RedemptionStatus,
)
from app.repositories.drink import DrinkRepository
from app.schemas.drink import RedeemDrinkRequest, SendDrinkOfferRequest
from app.services.events import EventPublisher
from app.use_cases.list_venue_menu import ListVenueMenuUseCase, VenueNotFoundError
from app.use_cases.redeem_drink import (
    RedeemDrinkUseCase,
    RedemptionExpiredError,
    RedemptionNotFoundError,
)
from app.use_cases.respond_to_drink_offer import (
    OfferExpiredError,
    OfferNotFoundError,
    RespondToDrinkOfferUseCase,
)
from app.use_cases.send_drink_offer import (
    BlockedError,
    MenuItemNotFoundError,
    MenuItemUnavailableError,
    NoActivePresenceError,
    NotSameVenueError,
    RecipientNotPresentError,
    SelfInteractionError,
    SendDrinkOfferUseCase,
    VerificationRequiredError,
)
from tests.conftest import (
    block_users,
    create_menu_item,
    create_session,
    create_user,
    create_venue,
)


class RecordingPublisher(EventPublisher):
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    async def publish(self, event_type: str, entity_id: str, actor_user_id: str | None = None):
        self.events.append((event_type, entity_id))


async def build_offer(session) -> tuple[str, str, str, str, DrinkOfferOrm]:
    """Creates venue, two users with presence, one menu item and one offer."""
    venue_id = await create_venue(session)
    sender_id = await create_user(session)
    recipient_id = await create_user(session)
    await create_session(session, sender_id, venue_id)
    recipient_presence = await create_session(session, recipient_id, venue_id)
    item_id = await create_menu_item(session, venue_id)
    publisher = RecordingPublisher()
    use_case = SendDrinkOfferUseCase(session, DrinkRepository(session), publisher=publisher)
    offer = await use_case.execute(
        user_id=sender_id,
        command=SendDrinkOfferRequest(
            recipientPresenceId=recipient_presence,
            menuItemId=item_id,
            idempotencyKey="key-1",
        ),
    )
    return sender_id, recipient_id, recipient_presence, item_id, offer


async def test_send_authorizes_payment_and_snapshots_item(db_session):
    _, _, _, _, offer = await build_offer(db_session)
    assert offer.status == DrinkOfferStatus.PAYMENT_AUTHORIZED
    assert offer.item_name_snapshot == "Negroni"
    assert offer.price_minor_snapshot == 350
    payment = await DrinkRepository(db_session).get_payment_by_offer(offer.id)
    assert payment is not None
    assert payment.status == PaymentStatus.AUTHORIZED
    assert payment.provider == "stub"
    assert payment.amount_minor == 350
    assert payment.idempotency_key == "key-1"


async def test_send_replay_is_idempotent(db_session):
    sender_id, _, _, _, offer = await build_offer(db_session)
    use_case = SendDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    replayed = await use_case.execute(
        user_id=sender_id,
        command=SendDrinkOfferRequest(
            recipientPresenceId=offer.recipient_presence_id,
            menuItemId=offer.menu_item_id,
            idempotencyKey="key-1",
        ),
    )
    assert replayed.id == offer.id
    payments = await db_session.execute(
        PaymentOrm.__table__.select().where(
            PaymentOrm.payer_user_id == sender_id,
            PaymentOrm.idempotency_key == "key-1",
        )
    )
    assert len(payments.all()) == 1


async def test_send_requires_active_sender_presence(db_session):
    sender_id = await create_user(db_session)
    venue_id = await create_venue(db_session)
    recipient_id = await create_user(db_session)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    use_case = SendDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(NoActivePresenceError):
        await use_case.execute(
            user_id=sender_id,
            command=SendDrinkOfferRequest(
                recipientPresenceId=recipient_presence,
                menuItemId=item_id,
                idempotencyKey="key-1",
            ),
        )


async def test_send_requires_verified_sender(db_session):
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session, verified=False)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    use_case = SendDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(VerificationRequiredError):
        await use_case.execute(
            user_id=sender_id,
            command=SendDrinkOfferRequest(
                recipientPresenceId=recipient_presence,
                menuItemId=item_id,
                idempotencyKey="key-2",
            ),
        )


async def test_send_rejects_unknown_recipient_presence(db_session):
    sender_id, _, _, item_id, _ = await build_offer(db_session)
    use_case = SendDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(RecipientNotPresentError):
        await use_case.execute(
            user_id=sender_id,
            command=SendDrinkOfferRequest(
                recipientPresenceId="no-such-presence",
                menuItemId=item_id,
                idempotencyKey="key-2",
            ),
        )


async def test_send_rejects_recipient_in_other_venue(db_session):
    sender_id, _, _, item_id, _ = await build_offer(db_session)
    other_venue_id = await create_venue(db_session)
    other_user_id = await create_user(db_session)
    other_presence = await create_session(db_session, other_user_id, other_venue_id)
    use_case = SendDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(NotSameVenueError):
        await use_case.execute(
            user_id=sender_id,
            command=SendDrinkOfferRequest(
                recipientPresenceId=other_presence,
                menuItemId=item_id,
                idempotencyKey="key-2",
            ),
        )


async def test_send_rejects_self_interaction(db_session):
    venue_id = await create_venue(db_session)
    user_id = await create_user(db_session)
    presence = await create_session(db_session, user_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    use_case = SendDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(SelfInteractionError):
        await use_case.execute(
            user_id=user_id,
            command=SendDrinkOfferRequest(
                recipientPresenceId=presence,
                menuItemId=item_id,
                idempotencyKey="key-1",
            ),
        )


async def test_send_rejects_blocked_recipient(db_session):
    sender_id, recipient_id, recipient_presence, item_id, _ = await build_offer(db_session)
    await block_users(db_session, sender_id, recipient_id)
    use_case = SendDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(BlockedError):
        await use_case.execute(
            user_id=sender_id,
            command=SendDrinkOfferRequest(
                recipientPresenceId=recipient_presence,
                menuItemId=item_id,
                idempotencyKey="key-2",
            ),
        )


async def test_send_rejects_item_from_another_venue(db_session):
    sender_id, _, recipient_presence, _, _ = await build_offer(db_session)
    other_venue_id = await create_venue(db_session)
    foreign_item_id = await create_menu_item(db_session, other_venue_id)
    use_case = SendDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(MenuItemUnavailableError):
        await use_case.execute(
            user_id=sender_id,
            command=SendDrinkOfferRequest(
                recipientPresenceId=recipient_presence,
                menuItemId=foreign_item_id,
                idempotencyKey="key-2",
            ),
        )


async def test_send_rejects_unavailable_item(db_session):
    sender_id, _, recipient_presence, _, _ = await build_offer(db_session)
    use_case = SendDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    venue_id = await create_venue(db_session)
    unavailable_item = await create_menu_item(db_session, venue_id, availability="unavailable")
    with pytest.raises(MenuItemUnavailableError):
        await use_case.execute(
            user_id=sender_id,
            command=SendDrinkOfferRequest(
                recipientPresenceId=recipient_presence,
                menuItemId=unavailable_item,
                idempotencyKey="key-2",
            ),
        )


async def test_send_rejects_unknown_item(db_session):
    sender_id, _, recipient_presence, _, _ = await build_offer(db_session)
    use_case = SendDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(MenuItemNotFoundError):
        await use_case.execute(
            user_id=sender_id,
            command=SendDrinkOfferRequest(
                recipientPresenceId=recipient_presence,
                menuItemId="no-such-item",
                idempotencyKey="key-2",
            ),
        )


async def test_send_emits_payment_and_offer_events(db_session):
    publisher = RecordingPublisher()
    venue_id = await create_venue(db_session)
    sender_id = await create_user(db_session)
    recipient_id = await create_user(db_session)
    await create_session(db_session, sender_id, venue_id)
    recipient_presence = await create_session(db_session, recipient_id, venue_id)
    item_id = await create_menu_item(db_session, venue_id)
    use_case = SendDrinkOfferUseCase(
        db_session, DrinkRepository(db_session), publisher=publisher
    )
    await use_case.execute(
        user_id=sender_id,
        command=SendDrinkOfferRequest(
            recipientPresenceId=recipient_presence,
            menuItemId=item_id,
            idempotencyKey="key-1",
        ),
    )
    assert [event for event, _ in publisher.events] == [
        "payment.authorized.v1",
        "drink_offer.created.v1",
    ]


async def test_accept_creates_redemption_with_code(db_session):
    _, recipient_id, _, _, offer = await build_offer(db_session)
    use_case = RespondToDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    updated, redemption, code = await use_case.execute(
        user_id=recipient_id, offer_id=offer.id, decision="accept"
    )
    assert updated.status == DrinkOfferStatus.ACCEPTED
    assert redemption is not None
    assert redemption.status == RedemptionStatus.CREATED
    assert redemption.code_hash != code
    assert code.isdigit() and len(code) == 6


async def test_decline_voids_payment(db_session):
    _, recipient_id, _, _, offer = await build_offer(db_session)
    use_case = RespondToDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    updated, redemption, code = await use_case.execute(
        user_id=recipient_id, offer_id=offer.id, decision="decline"
    )
    assert updated.status == DrinkOfferStatus.DECLINED
    assert redemption is None and code is None
    payment = await DrinkRepository(db_session).get_payment_by_offer(offer.id)
    assert payment.status == PaymentStatus.VOIDED


async def test_respond_hides_unknown_or_foreign_offers(db_session):
    sender_id, _, _, _, offer = await build_offer(db_session)
    use_case = RespondToDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(OfferNotFoundError):
        await use_case.execute(user_id=sender_id, offer_id=offer.id, decision="accept")
    with pytest.raises(OfferNotFoundError):
        await use_case.execute(user_id="no-such-user", offer_id=offer.id, decision="accept")


async def test_double_respond_is_rejected(db_session):
    _, recipient_id, _, _, offer = await build_offer(db_session)
    use_case = RespondToDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    await use_case.execute(user_id=recipient_id, offer_id=offer.id, decision="accept")
    with pytest.raises(Exception) as exc_info:
        await use_case.execute(user_id=recipient_id, offer_id=offer.id, decision="decline")
    assert type(exc_info.value).__name__ == "InvalidStateTransitionError"


async def test_expired_offer_cannot_be_responded(db_session):
    from datetime import UTC, datetime

    _, recipient_id, _, _, offer = await build_offer(db_session)
    offer.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)
    await db_session.flush()
    use_case = RespondToDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(OfferExpiredError):
        await use_case.execute(user_id=recipient_id, offer_id=offer.id, decision="accept")


async def test_redeem_captures_payment(db_session):
    _, recipient_id, _, _, offer = await build_offer(db_session)
    responder = RespondToDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    _, _redemption, code = await responder.execute(
        user_id=recipient_id, offer_id=offer.id, decision="accept"
    )
    use_case = RedeemDrinkUseCase(db_session, DrinkRepository(db_session))
    redeemed = await use_case.execute(
        user_id=recipient_id,
        command=RedeemDrinkRequest(redemptionCode=code, idempotencyKey="key-1"),
    )
    assert redeemed.status == RedemptionStatus.REDEEMED
    assert redeemed.redeemed_at is not None
    payment = await DrinkRepository(db_session).get_payment_by_offer(offer.id)
    assert payment.status == PaymentStatus.CAPTURED
    offer = await DrinkRepository(db_session).get_offer(offer.id)
    assert offer.status == DrinkOfferStatus.REDEEMED


async def test_redeem_replay_is_idempotent(db_session):
    _, recipient_id, _, _, offer = await build_offer(db_session)
    responder = RespondToDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    _, redemption, code = await responder.execute(
        user_id=recipient_id, offer_id=offer.id, decision="accept"
    )
    use_case = RedeemDrinkUseCase(db_session, DrinkRepository(db_session))
    first = await use_case.execute(
        user_id=recipient_id,
        command=RedeemDrinkRequest(redemptionCode=code, idempotencyKey="key-1"),
    )
    second = await use_case.execute(
        user_id=recipient_id,
        command=RedeemDrinkRequest(redemptionCode=code, idempotencyKey="key-2"),
    )
    assert second.id == first.id == redemption.id


async def test_redeem_rejects_unknown_code(db_session):
    use_case = RedeemDrinkUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(RedemptionNotFoundError):
        await use_case.execute(
            user_id="anyone",
            command=RedeemDrinkRequest(redemptionCode="000000", idempotencyKey="key-1"),
        )


async def test_redeem_before_accept_is_rejected(db_session):
    from hashlib import sha256

    from app.models.drink import RedemptionOrm

    _, _, _, _, offer = await build_offer(db_session)
    repo = DrinkRepository(db_session)

    redemption = RedemptionOrm(
        drink_offer_id=offer.id,
        code_hash=sha256(b"123456").hexdigest(),
        expires_at=offer.expires_at,
    )
    await repo.add_redemption(redemption)
    use_case = RedeemDrinkUseCase(db_session, repo)
    with pytest.raises(Exception) as exc_info:
        await use_case.execute(
            user_id="staff",
            command=RedeemDrinkRequest(redemptionCode="123456", idempotencyKey="key-1"),
        )
    assert type(exc_info.value).__name__ == "InvalidStateTransitionError"


async def test_redeem_rejects_expired_redemption(db_session):
    from datetime import UTC, datetime

    _, recipient_id, _, _, offer = await build_offer(db_session)
    responder = RespondToDrinkOfferUseCase(db_session, DrinkRepository(db_session))
    _, redemption, code = await responder.execute(
        user_id=recipient_id, offer_id=offer.id, decision="accept"
    )
    redemption.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)
    await db_session.flush()
    use_case = RedeemDrinkUseCase(db_session, DrinkRepository(db_session))
    with pytest.raises(RedemptionExpiredError):
        await use_case.execute(
            user_id=recipient_id,
            command=RedeemDrinkRequest(redemptionCode=code, idempotencyKey="key-1"),
        )


async def test_menu_lists_available_items_only(db_session):
    venue_id = await create_venue(db_session)
    other_venue_id = await create_venue(db_session)
    await create_menu_item(db_session, venue_id, name="Aperol")
    await create_menu_item(db_session, venue_id, name="Negroni", availability="unavailable")
    await create_menu_item(db_session, other_venue_id, name="Foreign")
    items = await ListVenueMenuUseCase(DrinkRepository(db_session)).execute(venue_id=venue_id)
    assert [item.name for item in items] == ["Aperol"]


async def test_menu_raises_for_unknown_venue(db_session):
    with pytest.raises(VenueNotFoundError):
        await ListVenueMenuUseCase(DrinkRepository(db_session)).execute(venue_id="nope")
