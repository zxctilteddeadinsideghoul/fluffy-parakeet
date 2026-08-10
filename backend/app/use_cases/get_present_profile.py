"""Use case: full profile of one present user."""

import logging
from datetime import UTC, datetime

from app.repositories.presence import PresenceRepository
from app.schemas.discovery import VisibleProfileDto
from app.use_cases.list_present_profiles import ViewerNotPresentError, to_dto

logger = logging.getLogger(__name__)


class ProfileNotFoundError(Exception):
    """Raised when the profile is not visible to the viewer."""


class GetPresentProfileUseCase:
    """Returns the full profile of a present user, or hides it neutrally."""

    def __init__(self, repository: PresenceRepository) -> None:
        self._repository = repository

    async def execute(
        self, *, presence_id: str, viewer_user_id: str
    ) -> VisibleProfileDto:
        logger.info("get present profile: presence=%s viewer=%s", presence_id, viewer_user_id)
        viewer_session = await self._repository.find_active_session(viewer_user_id)
        if viewer_session is None:
            raise ViewerNotPresentError()

        now = datetime.now(UTC).replace(tzinfo=None)
        present = await self._repository.get_present_profile(
            viewer_session.venue_id,
            presence_id,
            viewer_user_id,
            now,
        )
        if present is None:
            logger.info(
                "get present profile: presence=%s viewer=%s -> not visible",
                presence_id,
                viewer_user_id,
            )
            raise ProfileNotFoundError()
        logger.info(
            "get present profile: presence=%s viewer=%s -> user=%s",
            presence_id,
            viewer_user_id,
            present.user.id,
        )
        return to_dto(present)