"""Repository for the Identity context: User and Profile data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ApproachMode
from app.models.user import ProfileOrm, UserOrm


class IdentityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_auth_identity(self, provider: str, subject: str) -> UserOrm | None:
        stmt = select(UserOrm).where(
            UserOrm.auth_provider == provider,
            UserOrm.auth_subject == subject,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def create_user_with_profile(
        self,
        *,
        provider: str,
        subject: str,
        email_normalized: str | None = None,
    ) -> UserOrm:
        """Create a new account with an empty, non-visible profile (onboarding §5)."""
        user = UserOrm(
            auth_provider=provider,
            auth_subject=subject,
            email_normalized=email_normalized,
        )
        user.profile = ProfileOrm(
            display_name="",
            communication_goals="",
            default_approach_mode=ApproachMode.ASK_BEFORE_APPROACH,
            visibility_enabled=False,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def get_user(self, user_id: str) -> UserOrm | None:
        return await self._session.get(UserOrm, user_id)

    async def get_profile(self, user_id: str) -> ProfileOrm | None:
        stmt = select(ProfileOrm).where(ProfileOrm.user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def update(self, entity: UserOrm | ProfileOrm) -> None:
        self._session.add(entity)
        await self._session.flush()