"""Use cases: check-in (start presence) and check-out (end presence)."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256

from app.models.enums import CheckInMethod, PresenceStatus, UserStatus, VenueStatus
from app.models.presence import PresenceSession
from app.repositories.presence import PresenceRepository
from app.schemas.presence import CheckInCommand, PresenceSessionDto
from app.services.events import EventPublisher, event_publisher


class VenueNotFoundError(Exception):
    """Raised when the venue does not exist."""


class InvalidCheckInTokenError(Exception):
    """Raised when the check-in token is missing, revoked or expired."""


class PresenceAlreadyActiveError(Exception):
    """Raised when the user already has an active or hidden session."""


class PresenceNotActiveError(Exception):
    """Raised when the user has no active or hidden session to end."""


class UserNotActiveError(Exception):
    """Raised when the user account is not active."""


class VerificationRequiredError(Exception):
    """Raised when the user has no valid verification."""


def _to_dto(session: PresenceSession) -> PresenceSessionDto:
    return PresenceSessionDto(
        id=session.id,
        venue_id=session.venue_id,
        status=session.status,
        visibility=session.visibility,
        approach_mode=session.approach_mode,
        expires_at=session.expires_at,
    )


class CountPresentUsersUseCase:
    """Counts users currently visible to the viewer at a venue."""

    def __init__(self, repository: PresenceRepository):
        self.repository = repository

    def execute(self, venue_id: str, viewer_user_id: str | None = None) -> int:
        if not self.repository.venue_exists(venue_id):
            raise VenueNotFoundError(venue_id)
        now = datetime.now(UTC).replace(tzinfo=None).replace(tzinfo=None)
        return self.repository.count_visible_users(venue_id, viewer_user_id, now)


class CheckInUseCase:
    """Starts a presence session for the user at the venue behind the token."""

    def __init__(
        self,
        repository: PresenceRepository,
        ttl_hours: int,
        publisher: EventPublisher = event_publisher,
    ):
        self.repository = repository
        self.ttl_hours = ttl_hours
        self.publisher = publisher

    def execute(self, user_id: str, command: CheckInCommand) -> PresenceSessionDto:
        if self.repository.user_status(user_id) != UserStatus.ACTIVE:
            raise UserNotActiveError(user_id)
        if not self.repository.is_verified_user(user_id, datetime.now(UTC).replace(tzinfo=None)):
            raise VerificationRequiredError(user_id)

        now = datetime.now(UTC).replace(tzinfo=None)
        token = self.repository.find_active_token(
            sha256(command.venue_token.encode()).hexdigest(), now
        )
        if token is None:
            raise InvalidCheckInTokenError()
        if self.repository.venue_status(token.venue_id) != VenueStatus.ACTIVE.value:
            raise VenueNotFoundError(token.venue_id)
        if self.repository.find_active_session(user_id) is not None:
            raise PresenceAlreadyActiveError(user_id)

        session = self.repository.add_session(
            PresenceSession(
                user_id=user_id,
                venue_id=token.venue_id,
                status=PresenceStatus.ACTIVE,
                visibility=command.visibility,
                approach_mode=command.approach_mode,
                check_in_method=CheckInMethod.VENUE_QR,
                checked_in_at=now,
                last_heartbeat_at=now,
                expires_at=now + timedelta(hours=self.ttl_hours),
            )
        )
        self.publisher.publish("presence.started.v1", session.id, user_id)
        return _to_dto(session)


class CheckOutUseCase:
    """Ends the user's current presence session."""

    def __init__(self, repository: PresenceRepository, publisher: EventPublisher = event_publisher):
        self.repository = repository
        self.publisher = publisher

    def execute(self, user_id: str) -> PresenceSessionDto:
        session = self.repository.find_active_session(user_id)
        if session is None:
            raise PresenceNotActiveError(user_id)
        session.status = PresenceStatus.ENDED
        session.ended_at = datetime.now(UTC).replace(tzinfo=None)
        self.repository.db.flush()
        self.publisher.publish("presence.ended.v1", session.id, user_id)
        return _to_dto(session)
