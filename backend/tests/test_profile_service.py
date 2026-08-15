"""Service tests for the own-profile read/update use cases."""


from datetime import date, timedelta

import pytest

from app.models.enums import (
    ApproachMode,
    CommunicationGoal,
    MediaModerationStatus,
)
from app.repositories.identity import IdentityRepository
from app.schemas.profile import UpdateMyProfileRequest
from app.use_cases.get_my_profile import GetMyProfileUseCase, UserNotFoundError
from app.use_cases.update_my_profile import (
    ProfileValidationError,
    UpdateMyProfileUseCase,
)
from tests.conftest import create_photo, create_user, utcnow


def make_get_use_case(session) -> GetMyProfileUseCase:
    return GetMyProfileUseCase(IdentityRepository(session))


def make_update_use_case(session) -> UpdateMyProfileUseCase:
    return UpdateMyProfileUseCase(IdentityRepository(session))


async def test_get_returns_profile_with_age_and_verified_flag(db_session):
    user_id = await create_user(db_session)

    result = await make_get_use_case(db_session).execute(user_id=user_id)

    assert result.id == user_id
    assert result.age == 26
    assert result.verification == {"isVerified": True}
    assert result.defaultApproachMode == ApproachMode.ASK_BEFORE_APPROACH


async def test_get_unverified_user_has_no_birth_date(db_session):
    user_id = await create_user(db_session, verified=False, birth_date=None)

    result = await make_get_use_case(db_session).execute(user_id=user_id)

    assert result.age is None
    assert result.verification == {"isVerified": False}


async def test_get_includes_photo_moderation_status(db_session):
    user_id = await create_user(db_session)
    await create_photo(
        db_session,
        user_id,
        moderation=MediaModerationStatus.PENDING,
        url="https://cdn.example/pending.jpg",
    )

    result = await make_get_use_case(db_session).execute(user_id=user_id)

    assert len(result.photos) == 1
    assert result.photos[0].url == "https://cdn.example/pending.jpg"
    assert result.photos[0].moderationStatus == MediaModerationStatus.PENDING


async def test_get_ignores_approved_verification_that_expired(db_session):
    from app.models.enums import VerificationStatus, VerificationType
    from app.models.user import VerificationOrm

    user_id = await create_user(db_session, verified=False)
    db_session.add(
        VerificationOrm(
            user_id=user_id,
            type=VerificationType.PHOTO,
            status=VerificationStatus.APPROVED,
            verified_at=utcnow() - timedelta(days=90),
            expires_at=utcnow() - timedelta(days=30),
        )
    )
    await db_session.flush()

    result = await make_get_use_case(db_session).execute(user_id=user_id)
    assert result.verification == {"isVerified": False}


async def test_visible_profile_requires_display_name(db_session):
    user_id = await create_user(db_session)
    command = UpdateMyProfileRequest(
        displayName="   ",
        communicationGoals=[CommunicationGoal.FRIENDS],
        defaultApproachMode=ApproachMode.MAY_APPROACH,
        visibilityEnabled=True,
    )

    with pytest.raises(ProfileValidationError):
        await make_update_use_case(db_session).execute(user_id=user_id, command=command)


async def test_hidden_profile_allows_empty_display_name(db_session):
    user_id = await create_user(db_session)
    command = UpdateMyProfileRequest(
        displayName="",
        communicationGoals=[],
        defaultApproachMode=ApproachMode.CHAT_ONLY,
        visibilityEnabled=False,
    )

    result = await make_update_use_case(db_session).execute(user_id=user_id, command=command)

    assert result.displayName == ""
    assert result.communicationGoals == []
    assert result.defaultApproachMode == ApproachMode.CHAT_ONLY


async def test_update_trims_name_and_persists_goals(db_session):
    user_id = await create_user(db_session)
    command = UpdateMyProfileRequest(
        displayName="  Alice  ",
        communicationGoals=[CommunicationGoal.FRIENDS, CommunicationGoal.NETWORKING],
        defaultApproachMode=ApproachMode.ASK_BEFORE_APPROACH,
        visibilityEnabled=True,
    )

    result = await make_update_use_case(db_session).execute(user_id=user_id, command=command)

    assert result.displayName == "Alice"
    assert result.communicationGoals == [
        CommunicationGoal.FRIENDS,
        CommunicationGoal.NETWORKING,
    ]
    profile = await IdentityRepository(db_session).get_profile(user_id)
    assert profile.communication_goals == "friends,networking"


async def test_update_saves_birth_date(db_session):
    user_id = await create_user(db_session, birth_date=None)
    command = UpdateMyProfileRequest(
        displayName="Bob",
        communicationGoals=[],
        defaultApproachMode=ApproachMode.CHAT_ONLY,
        visibilityEnabled=True,
        birthDate=date(1990, 1, 1),
    )

    await make_update_use_case(db_session).execute(user_id=user_id, command=command)

    result = await make_get_use_case(db_session).execute(user_id=user_id)
    assert result.age == 36


async def test_update_unknown_user_raises(db_session):
    command = UpdateMyProfileRequest(
        displayName="Ghost",
        communicationGoals=[],
        defaultApproachMode=ApproachMode.CHAT_ONLY,
        visibilityEnabled=True,
    )
    with pytest.raises(UserNotFoundError):
        await make_update_use_case(db_session).execute(user_id="missing", command=command)