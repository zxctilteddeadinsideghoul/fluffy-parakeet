"""HTTP routes for the Communication context (thin: only HTTP concerns)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.communication import ContactRequestOrm, MessageOrm
from app.routes.dependencies import (
    get_current_user_id,
    get_list_conversations_use_case,
    get_list_messages_use_case,
    get_list_my_contact_requests_use_case,
    get_respond_to_contact_request_use_case,
    get_send_contact_request_use_case,
    get_send_message_use_case,
)
from app.schemas.base import SuccessEnvelope
from app.schemas.communication import (
    ContactRequestDto,
    ConversationDto,
    MessageDto,
    MessagesPageDto,
    RespondContactRequestRequest,
    SendContactRequestRequest,
    SendMessageRequest,
)
from app.use_cases.list_conversations import ListConversationsUseCase
from app.use_cases.list_messages import (
    ConversationNotFoundError as MessagesConversationNotFoundError,
)
from app.use_cases.list_messages import (
    InvalidCursorError,
    ListMessagesUseCase,
)
from app.use_cases.list_my_contact_requests import (
    ListMyContactRequestsUseCase,
    request_to_dto,
)
from app.use_cases.respond_to_contact_request import (
    InvalidStateTransitionError as RespondInvalidStateTransitionError,
)
from app.use_cases.respond_to_contact_request import (
    RequestExpiredError,
    RequestNotFoundError,
    RespondToContactRequestUseCase,
)
from app.use_cases.send_contact_request import (
    BlockedError,
    NoActivePresenceError,
    NotSameVenueError,
    RecipientNotPresentError,
    RequestAlreadyExistsError,
    SelfInteractionError,
    SendContactRequestUseCase,
    UserNotActiveError,
    VerificationRequiredError,
)
from app.use_cases.send_message import (
    ConversationNotFoundError as SendConversationNotFoundError,
)
from app.use_cases.send_message import (
    InvalidStateTransitionError as SendInvalidStateTransitionError,
)
from app.use_cases.send_message import (
    NotMemberError,
    SendMessageUseCase,
)

router = APIRouter(tags=["communication"])


@router.post(
    "/me/contact-requests",
    response_model=SuccessEnvelope[ContactRequestDto],
    status_code=201,
)
async def send_contact_request(
    payload: SendContactRequestRequest,
    use_case: SendContactRequestUseCase = Depends(get_send_contact_request_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[ContactRequestDto]:
    try:
        request: ContactRequestOrm = await use_case.execute(user_id=user_id, command=payload)
    except (UserNotActiveError, VerificationRequiredError, BlockedError):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "FORBIDDEN") from None
    except NoActivePresenceError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "ACTIVE_PRESENCE_REQUIRED"
        ) from None
    except (RecipientNotPresentError, NotSameVenueError):
        raise HTTPException(status.HTTP_409_CONFLICT, "NOT_SAME_VENUE") from None
    except SelfInteractionError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "INVALID_STATE_TRANSITION"
        ) from None
    except RequestAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "REQUEST_ALREADY_EXISTS"
        ) from None
    return SuccessEnvelope(data=request_to_dto(request))


@router.post(
    "/me/contact-requests/{request_id}/response",
    response_model=SuccessEnvelope[ContactRequestDto],
)
async def respond_to_contact_request(
    request_id: str,
    payload: RespondContactRequestRequest,
    use_case: RespondToContactRequestUseCase = Depends(
        get_respond_to_contact_request_use_case
    ),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[ContactRequestDto]:
    try:
        request = await use_case.execute(
            user_id=user_id, request_id=request_id, decision=payload.decision
        )
    except RequestNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    except RequestExpiredError:
        raise HTTPException(status.HTTP_409_CONFLICT, "OFFER_EXPIRED") from None
    except RespondInvalidStateTransitionError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "INVALID_STATE_TRANSITION"
        ) from None
    return SuccessEnvelope(data=request_to_dto(request))


@router.get(
    "/me/contact-requests",
    response_model=SuccessEnvelope[list[ContactRequestDto]],
)
async def list_my_contact_requests(
    use_case: ListMyContactRequestsUseCase = Depends(
        get_list_my_contact_requests_use_case
    ),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[list[ContactRequestDto]]:
    return SuccessEnvelope(data=await use_case.execute(user_id=user_id))


@router.get(
    "/me/conversations",
    response_model=SuccessEnvelope[list[ConversationDto]],
)
async def list_conversations(
    use_case: ListConversationsUseCase = Depends(get_list_conversations_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[list[ConversationDto]]:
    return SuccessEnvelope(data=await use_case.execute(user_id=user_id))


@router.post(
    "/me/conversations/{conversation_id}/messages",
    response_model=SuccessEnvelope[MessageDto],
    status_code=201,
)
async def send_message(
    conversation_id: str,
    payload: SendMessageRequest,
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[MessageDto]:
    try:
        message: MessageOrm = await use_case.execute(
            user_id=user_id, conversation_id=conversation_id, command=payload
        )
    except SendConversationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    except NotMemberError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "FORBIDDEN") from None
    except SendInvalidStateTransitionError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "INVALID_STATE_TRANSITION"
        ) from None
    return SuccessEnvelope(
        data=MessageDto(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_user_id=message.sender_user_id,
            type=message.type,
            body=message.body,
            created_at=message.created_at,
        )
    )


@router.get(
    "/me/conversations/{conversation_id}/messages",
    response_model=SuccessEnvelope[MessagesPageDto],
)
async def list_messages(
    conversation_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    use_case: ListMessagesUseCase = Depends(get_list_messages_use_case),
    user_id: str = Depends(get_current_user_id),
) -> SuccessEnvelope[MessagesPageDto]:
    try:
        page = await use_case.execute(
            user_id=user_id,
            conversation_id=conversation_id,
            limit=limit,
            cursor=cursor,
        )
    except MessagesConversationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NOT_FOUND") from None
    except InvalidCursorError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "INVALID_CURSOR") from None
    return SuccessEnvelope(data=page)
