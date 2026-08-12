"""Dependency injection container: builds the whole object graph."""

from dependency_injector import containers, providers  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.drink import DrinkRepository
from app.repositories.identity import IdentityRepository
from app.repositories.presence import PresenceRepository
from app.services.events import EventPublisher
from app.services.payments import PaymentGateway
from app.storage.local import LocalPhotoStorage
from app.storage.minio_storage import MinioPhotoStorage
from app.use_cases.check_in import CheckInUseCase
from app.use_cases.check_out import CheckOutUseCase
from app.use_cases.count_present_users import CountPresentUsersUseCase
from app.use_cases.delete_profile_photo import DeleteProfilePhotoUseCase
from app.use_cases.get_my_profile import GetMyProfileUseCase
from app.use_cases.get_present_profile import GetPresentProfileUseCase
from app.use_cases.list_my_drink_offers import ListMyDrinkOffersUseCase
from app.use_cases.list_present_profiles import ListPresentProfilesUseCase
from app.use_cases.list_venue_menu import ListVenueMenuUseCase
from app.use_cases.redeem_drink import RedeemDrinkUseCase
from app.use_cases.respond_to_drink_offer import RespondToDrinkOfferUseCase
from app.use_cases.send_drink_offer import SendDrinkOfferUseCase
from app.use_cases.sign_in_or_register import SignInOrRegisterUseCase
from app.use_cases.update_my_profile import UpdateMyProfileUseCase
from app.use_cases.upload_profile_photo import UploadProfilePhotoUseCase


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

    identity_repository = providers.Factory(
        IdentityRepository,
        session=db_session,
    )

    drink_repository = providers.Factory(
        DrinkRepository,
        session=db_session,
    )

    payment_gateway = providers.Singleton(PaymentGateway)

    photo_storage = providers.Singleton(
        MinioPhotoStorage
        if settings.photo_storage_backend == "minio"
        else LocalPhotoStorage
    )

    upload_profile_photo_use_case = providers.Factory(
        UploadProfilePhotoUseCase,
        repository=identity_repository,
        storage=photo_storage,
        max_upload_bytes=settings.max_photo_upload_bytes,
        auto_approve=settings.environment == "development",
    )

    delete_profile_photo_use_case = providers.Factory(
        DeleteProfilePhotoUseCase,
        repository=identity_repository,
    )

    sign_in_or_register_use_case = providers.Factory(
        SignInOrRegisterUseCase,
        identity_repository=identity_repository,
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

    get_my_profile_use_case = providers.Factory(
        GetMyProfileUseCase,
        repository=identity_repository,
    )

    update_my_profile_use_case = providers.Factory(
        UpdateMyProfileUseCase,
        repository=identity_repository,
    )

    send_drink_offer_use_case = providers.Factory(
        SendDrinkOfferUseCase,
        session=db_session,
        repository=drink_repository,
        offer_ttl_minutes=settings.drink_offer_ttl_minutes,
        requires_connection=settings.drink_offer_requires_connection,
        gateway=payment_gateway,
        publisher=event_publisher,
    )

    respond_to_drink_offer_use_case = providers.Factory(
        RespondToDrinkOfferUseCase,
        session=db_session,
        repository=drink_repository,
        redemption_ttl_minutes=settings.redemption_ttl_minutes,
        gateway=payment_gateway,
        publisher=event_publisher,
    )

    redeem_drink_use_case = providers.Factory(
        RedeemDrinkUseCase,
        session=db_session,
        repository=drink_repository,
        gateway=payment_gateway,
        publisher=event_publisher,
    )

    list_venue_menu_use_case = providers.Factory(
        ListVenueMenuUseCase,
        repository=drink_repository,
    )

    list_my_drink_offers_use_case = providers.Factory(
        ListMyDrinkOffersUseCase,
        repository=drink_repository,
    )