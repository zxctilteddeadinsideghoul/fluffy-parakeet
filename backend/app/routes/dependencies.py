"""Route dependencies: use case providers and trusted auth headers."""

from typing import Annotated

from dependency_injector import providers  # type: ignore
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.containers.container import Container
from app.core.config import settings
from app.core.db import get_db_session
from app.use_cases.check_in import CheckInUseCase
from app.use_cases.check_out import CheckOutUseCase
from app.use_cases.count_present_users import CountPresentUsersUseCase
from app.use_cases.get_my_profile import GetMyProfileUseCase
from app.use_cases.get_present_profile import GetPresentProfileUseCase
from app.use_cases.list_present_profiles import ListPresentProfilesUseCase
from app.use_cases.sign_in_or_register import SignInOrRegisterUseCase
from app.use_cases.update_my_profile import UpdateMyProfileUseCase


def get_current_user_id(
    x_dev_user_id: Annotated[str | None, Header()] = None,
) -> str:
    """Current user from the server context.

    Until real authentication exists, the user id is taken from a dev-only
    header that is accepted exclusively in the development environment.
    """
    if settings.environment == "development" and x_dev_user_id:
        return x_dev_user_id
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTH_REQUIRED")


def get_container(request: Request) -> Container:
    return request.app.container  # type: ignore[attr-defined]


def _build_with_session(
    container: Container, provider, session: AsyncSession
):
    with container.db_session.override(providers.Object(session)):
        return provider()


def get_check_in_use_case(
    session: AsyncSession = Depends(get_db_session),
    container: Container = Depends(get_container),
) -> CheckInUseCase:
    return _build_with_session(container, container.check_in_use_case, session)


def get_check_out_use_case(
    session: AsyncSession = Depends(get_db_session),
    container: Container = Depends(get_container),
) -> CheckOutUseCase:
    return _build_with_session(container, container.check_out_use_case, session)


def get_count_present_users_use_case(
    session: AsyncSession = Depends(get_db_session),
    container: Container = Depends(get_container),
) -> CountPresentUsersUseCase:
    return _build_with_session(container, container.count_present_users_use_case, session)


def get_list_present_profiles_use_case(
    session: AsyncSession = Depends(get_db_session),
    container: Container = Depends(get_container),
) -> ListPresentProfilesUseCase:
    return _build_with_session(container, container.list_present_profiles_use_case, session)


def get_present_profile_use_case(
    session: AsyncSession = Depends(get_db_session),
    container: Container = Depends(get_container),
) -> GetPresentProfileUseCase:
    return _build_with_session(container, container.get_present_profile_use_case, session)


def get_sign_in_or_register_use_case(
    session: AsyncSession = Depends(get_db_session),
    container: Container = Depends(get_container),
) -> SignInOrRegisterUseCase:
    return _build_with_session(container, container.sign_in_or_register_use_case, session)


def get_get_my_profile_use_case(
    session: AsyncSession = Depends(get_db_session),
    container: Container = Depends(get_container),
) -> GetMyProfileUseCase:
    return _build_with_session(container, container.get_my_profile_use_case, session)


def get_update_my_profile_use_case(
    session: AsyncSession = Depends(get_db_session),
    container: Container = Depends(get_container),
) -> UpdateMyProfileUseCase:
    return _build_with_session(container, container.update_my_profile_use_case, session)