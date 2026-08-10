"""Dependency injection container: builds the whole object graph."""

from dependency_injector import containers, providers  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.presence import PresenceRepository
from app.services.events import EventPublisher
from app.use_cases.check_in import CheckInUseCase
from app.use_cases.check_out import CheckOutUseCase
from app.use_cases.count_present_users import CountPresentUsersUseCase
from app.use_cases.get_present_profile import GetPresentProfileUseCase
from app.use_cases.list_present_profiles import ListPresentProfilesUseCase


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.routes.dependencies",
        ]
    )

    db_session = providers.Dependency(instance_of=AsyncSession)

    presence_repository = providers.Factory(
        PresenceRepository,
        session=db_session,
    )

    event_publisher = providers.Singleton(EventPublisher)

    check_in_use_case = providers.Factory(
        CheckInUseCase,
        session=db_session,
        repository=presence_repository,
        ttl_hours=settings.presence_ttl_hours,
        publisher=event_publisher,
    )

    check_out_use_case = providers.Factory(
        CheckOutUseCase,
        session=db_session,
        repository=presence_repository,
        publisher=event_publisher,
    )

    count_present_users_use_case = providers.Factory(
        CountPresentUsersUseCase,
        repository=presence_repository,
    )

    list_present_profiles_use_case = providers.Factory(
        ListPresentProfilesUseCase,
        repository=presence_repository,
    )

    get_present_profile_use_case = providers.Factory(
        GetPresentProfileUseCase,
        repository=presence_repository,
    )