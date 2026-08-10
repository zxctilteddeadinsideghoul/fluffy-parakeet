"""Service tests for sign-in-or-register identity use case."""

import pytest

from app.repositories.identity import IdentityRepository
from app.use_cases.sign_in_or_register import (
    InvalidAuthSubjectError,
    SignInOrRegisterUseCase,
)


def make_use_case(session) -> SignInOrRegisterUseCase:
    return SignInOrRegisterUseCase(IdentityRepository(session))


async def test_register_creates_user_with_hidden_profile(db_session):
    use_case = make_use_case(db_session)
    repo = IdentityRepository(db_session)

    user = await use_case.execute(provider="yandex", subject="ya-123")

    assert user.id
    assert user.auth_provider == "yandex"
    assert user.auth_subject == "ya-123"
    profile = await repo.get_profile(user.id)
    assert profile is not None
    assert profile.visibility_enabled is False


async def test_sign_in_returns_existing_user(db_session):
    use_case = make_use_case(db_session)
    first = await use_case.execute(provider="vk", subject="vk-1")

    second = await use_case.execute(provider="vk", subject="vk-1")

    assert second.id == first.id


async def test_register_email_saves_normalized_email(db_session):
    use_case = make_use_case(db_session)

    user = await use_case.execute(
        provider="email", subject="ME@Example.com", email="ME@Example.com"
    )

    assert user.email_normalized == "me@example.com"


async def test_empty_subject_is_rejected(db_session):
    use_case = make_use_case(db_session)

    with pytest.raises(InvalidAuthSubjectError):
        await use_case.execute(provider="email", subject="   ")