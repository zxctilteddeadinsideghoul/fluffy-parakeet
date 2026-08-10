"""Use case: sign in or register via a verified auth provider."""

import logging

from app.models.user import UserOrm
from app.repositories.identity import IdentityRepository

logger = logging.getLogger(__name__)


class InvalidAuthSubjectError(Exception):
    """Raised when the auth subject is empty or malformed."""


class SignInOrRegisterUseCase:
    """Find an account by (authProvider, authSubject) or create it with an empty profile."""

    def __init__(self, identity_repository: IdentityRepository) -> None:
        self._identity = identity_repository

    async def execute(
        self,
        *,
        provider: str,
        subject: str,
        email: str | None = None,
    ) -> UserOrm:
        subject = subject.strip()
        if not subject:
            raise InvalidAuthSubjectError()

        email_normalized = email.strip().lower() if email else None
        user = await self._identity.find_by_auth_identity(provider, subject)
        if user is not None:
            logger.info("sign in: provider=%s subject=%s -> user=%s", provider, subject, user.id)
            return user

        user = await self._identity.create_user_with_profile(
            provider=provider,
            subject=subject,
            email_normalized=email_normalized,
        )
        logger.info(
            "register: provider=%s subject=%s -> user=%s", provider, subject, user.id
        )
        return user