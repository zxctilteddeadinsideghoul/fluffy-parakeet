"""Use case: page of present users' profiles for the swipe deck."""

import base64
import json
from datetime import UTC, datetime

from app.models.enums import CommunicationGoal
from app.repositories.presence import PresenceRepository
from app.schemas.discovery import ProfilePhotoDto, VisibleProfileDto
from app.services.policy import available_actions


class VenueNotFoundError(Exception):
    """Raised when the venue does not exist."""


class ViewerNotPresentError(Exception):
    """Raised when the viewer has no active presence at the venue."""


class InvalidCursorError(Exception):
    """Raised when the pagination cursor cannot be parsed."""


def age(birth_date) -> int:
    today = datetime.now(UTC).replace(tzinfo=None).date()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def encode_cursor(checked_in_at: datetime, session_id: str) -> str:
    payload = json.dumps({"t": checked_in_at.isoformat(), "id": session_id})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        data = json.loads(raw)
        return datetime.fromisoformat(data["t"]), str(data["id"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise InvalidCursorError() from None


def _goals(raw: str) -> list[CommunicationGoal]:
    goals = []
    for part in raw.split(","):
        try:
            goals.append(CommunicationGoal(part))
        except ValueError:
            continue
    return goals


def to_dto(present) -> VisibleProfileDto:
    return VisibleProfileDto(
        userId=present.user.id,
        presenceId=present.session.id,
        venueId=present.session.venue_id,
        displayName=present.profile.display_name,
        age=age(present.user.birth_date),
        gender=present.profile.gender,
        bio=present.profile.bio,
        communicationGoals=_goals(present.profile.communication_goals),
        approachMode=present.session.approach_mode,
        photos=[
            ProfilePhotoDto(id=p.id, url=p.public_url or "", position=p.position)
            for p in present.photos
        ],
        isVerified=present.is_verified,
        availableActions=available_actions(present.session.approach_mode),
    )


class ListPresentProfilesUseCase:
    """Returns a page of present users visible to the viewer at the venue."""

    def __init__(self, repository: PresenceRepository) -> None:
        self._repository = repository

    async def execute(
        self, *, venue_id: str, viewer_user_id: str, limit: int, cursor: str | None
    ) -> tuple[list[VisibleProfileDto], str | None]:
        if not await self._repository.venue_exists(venue_id):
            raise VenueNotFoundError()

        viewer_session = await self._repository.find_active_session(viewer_user_id)
        if viewer_session is None or viewer_session.venue_id != venue_id:
            raise ViewerNotPresentError()

        after = decode_cursor(cursor) if cursor is not None else None
        now = datetime.now(UTC).replace(tzinfo=None)
        present_profiles, has_more = await self._repository.list_visible_profiles(
            venue_id,
            viewer_user_id,
            now,
            limit=limit,
            after=after,
        )
        items = [to_dto(present) for present in present_profiles]
        next_cursor = None
        if has_more and present_profiles:
            last = present_profiles[-1]
            next_cursor = encode_cursor(last.session.checked_in_at, last.session.id)
        return items, next_cursor