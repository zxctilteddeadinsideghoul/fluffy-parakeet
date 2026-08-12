"""Use case: list the current user's contact requests with their statuses."""

import logging

from app.repositories.communication import CommunicationRepository
from app.schemas.communication import ContactRequestDto

logger = logging.getLogger(__name__)


def request_to_dto(request) -> ContactRequestDto:
    return ContactRequestDto(
        id=request.id,
        sender_user_id=request.sender_user_id,
        recipient_user_id=request.recipient_user_id,
        sender_presence_id=request.sender_presence_id,
        recipient_presence_id=request.recipient_presence_id,
        venue_id=request.venue_id,
        status=request.status,
        message=request.message,
        created_at=request.created_at,
        responded_at=request.responded_at,
        expires_at=request.expires_at,
    )


class ListMyContactRequestsUseCase:
    """Returns requests the user sent or received, newest first."""

    def __init__(self, repository: CommunicationRepository) -> None:
        self._repository = repository

    async def execute(self, *, user_id: str) -> list[ContactRequestDto]:
        requests = await self._repository.list_requests_for_user(user_id)
        return [request_to_dto(request) for request in requests]
