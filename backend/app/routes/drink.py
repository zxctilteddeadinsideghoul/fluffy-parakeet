"""HTTP routes for the Commerce context (thin: only HTTP concerns)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.drink import DrinkOfferOrm, RedemptionOrm
from app.routes.dependencies import (
    get_current_user_id,
    get_list_my_drink_offers_use_case,
    get_list_venue_menu_use_case,
    get_redeem_drink_use_case,
    get_respond_to_drink_offer_use_case,
    get_send_drink_offer_use_case,
)
from app.schemas.base import SuccessEnvelope
from app.schemas.drink import (
    DrinkOfferDto,
    DrinkOfferResponseDto,
    MenuItemDto,
    RedeemDrinkRequest,
    RedemptionCreatedDto,
    RedemptionDto,
    RespondToDrinkOfferRequest,
    SendDrinkOfferRequest,
)
from app.use_cases.list_my_drink_offers import (
    ListMyDrinkOffersUseCase,
    offer_to_dto,
)
from app.use_cases.list_venue_menu import ListVenueMenuUseCase, VenueNotFoundError
from app.use_cases.redeem_drink import (
    InvalidStateTransitionError as RedeemInvalidStateTransitionError,
)
from app.use_cases.redeem_drink import (
    RedeemDrinkUseCase,
    RedemptionExpiredError,
    RedemptionNotFoundError,
)
from app.use_cases.respond_to_drink_offer import (
    InvalidStateTransitionError as RespondInvalidStateTransitionError,
)
from app.use_cases.respond_to_drink_offer import (
    OfferExpiredError,
    OfferNotFoundError,
    RespondToDrinkOfferUseCase,
)
from app.use_cases.send_drink_offer import (
    BlockedError,
    ConnectionRequiredError,
    MenuItemNotFoundError,
    MenuItemUnavailableError,
    NoActivePresenceError,
    NotSameVenueError,
    RecipientNotPresentError,
    SelfInteractionError,
    SendDrinkOfferUseCase,
    UserNotActiveError,
    VerificationRequiredError,
)

router = APIRouter(tags=["drinks"])


def _offer_dto(offer: DrinkOfferOrm) -> DrinkOfferDto:
    return offer_to_dto(offer)


@router.get(
    "/venues/{venue_id}/menu",
    response_model=SuccessEnvelope[list[MenuItemDto]],
)
async def list_venue_menu(
    venue_id: str,
    use_case: ListVenueMenuUseCase = Depends(get_list_venue_menu_use_case),
) -> SuccessEnvelope[list[MenuItemDto]]:
    try:
        items = await use_case.execute(venue_id=venue_id)
    except VenueNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    return SuccessEnvelope(data=items)


@router.get(
    "/me/drink-offers",
    response_model=SuccessEnvelope[list[DrinkOfferDto]],
)
async def list_my_drink_offers(
    use_case: ListMyDrinkOffersUseCase = Depends(get_list_my_drink_offers_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[list[DrinkOfferDto]]:
    offers = await use_case.execute(user_id=user_id)
    return SuccessEnvelope(data=offers)


@router.post(
    "/me/drink-offers",
    response_model=SuccessEnvelope[DrinkOfferDto],
    status_code=201,
)
async def send_drink_offer(
    payload: SendDrinkOfferRequest,
    use_case: SendDrinkOfferUseCase = Depends(get_send_drink_offer_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[DrinkOfferDto]:
    try:
        offer = await use_case.execute(user_id=user_id, command=payload)
    except (UserNotActiveError, VerificationRequiredError, BlockedError):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "FORBIDDEN") from None
    except (NoActivePresenceError, ConnectionRequiredError):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "ACTIVE_PRESENCE_REQUIRED"
        ) from None
    except (RecipientNotPresentError, NotSameVenueError):
        raise HTTPException(status.HTTP_409_CONFLICT, "NOT_SAME_VENUE") from None
    except SelfInteractionError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "INVALID_STATE_TRANSITION"
        ) from None
    except MenuItemNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    except MenuItemUnavailableError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "MENU_ITEM_UNAVAILABLE"
        ) from None
    return SuccessEnvelope(data=_offer_dto(offer))


@router.post(
    "/me/drink-offers/{offer_id}/response",
    response_model=SuccessEnvelope[DrinkOfferResponseDto],
)
async def respond_to_drink_offer(
    offer_id: str,
    payload: RespondToDrinkOfferRequest,
    use_case: RespondToDrinkOfferUseCase = Depends(get_respond_to_drink_offer_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[DrinkOfferResponseDto]:
    try:
        offer, redemption, code = await use_case.execute(
            user_id=user_id, offer_id=offer_id, decision=payload.decision
        )
    except OfferNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    except OfferExpiredError:
        raise HTTPException(status.HTTP_409_CONFLICT, "OFFER_EXPIRED") from None
    except RespondInvalidStateTransitionError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "INVALID_STATE_TRANSITION"
        ) from None
    data = DrinkOfferResponseDto(offer=_offer_dto(offer))
    if redemption is not None and code is not None:
        data.redemption = RedemptionCreatedDto(
            id=redemption.id,
            drink_offer_id=redemption.drink_offer_id,
            code=code,
            status=redemption.status,
            expires_at=redemption.expires_at,
        )
    return SuccessEnvelope(data=data)


@router.post(
    "/me/redemptions",
    response_model=SuccessEnvelope[RedemptionDto],
)
async def redeem_drink(
    payload: RedeemDrinkRequest,
    use_case: RedeemDrinkUseCase = Depends(get_redeem_drink_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[RedemptionDto]:
    try:
        redemption: RedemptionOrm = await use_case.execute(user_id=user_id, command=payload)
    except RedemptionNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    except (RedemptionExpiredError, RedeemInvalidStateTransitionError):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "REDEMPTION_EXPIRED"
        ) from None
    return SuccessEnvelope(
        data=RedemptionDto(
            id=redemption.id,
            drink_offer_id=redemption.drink_offer_id,
            status=redemption.status,
            expires_at=redemption.expires_at,
            redeemed_at=redemption.redeemed_at,
        )
    )
