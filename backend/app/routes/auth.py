"""Authentication routes: sign in or register via a verified auth provider."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field

from app.routes.dependencies import get_sign_in_or_register_use_case
from app.schemas.base import ApiModel, SuccessEnvelope
from app.use_cases.sign_in_or_register import (
    InvalidAuthSubjectError,
    SignInOrRegisterUseCase,
)

router = APIRouter(tags=["auth"])

AuthProviderValue = Literal["email", "yandex", "vk"]


class SignInRequest(ApiModel):
    auth_provider: AuthProviderValue = Field(alias="authProvider")
    auth_subject: str = Field(alias="authSubject", min_length=1)
    email: str | None = None


class AuthResponseDto(ApiModel):
    user_id: str = Field(alias="userId")
    is_new_user: bool = Field(alias="isNewUser")


@router.post("/auth/sign-in", response_model=SuccessEnvelope[AuthResponseDto])
async def sign_in(
    payload: SignInRequest,
    use_case: SignInOrRegisterUseCase = Depends(get_sign_in_or_register_use_case),
) -> SuccessEnvelope[AuthResponseDto]:
    try:
        result = await use_case.execute(
            provider=payload.auth_provider,
            subject=payload.auth_subject,
            email=payload.email,
        )
    except InvalidAuthSubjectError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR"
        ) from None
    return SuccessEnvelope(
        data=AuthResponseDto(userId=result.user.id, isNewUser=result.is_new_user)
    )