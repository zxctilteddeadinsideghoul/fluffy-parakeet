"""API dependencies."""

from typing import Annotated

from fastapi import Header, HTTPException

from app.core.config import settings

AUTH_HEADER = "x-dev-user-id"


def get_current_user_id(
    x_dev_user_id: Annotated[str | None, Header()] = None,
) -> str:
    """Current user from the server context.

    Until real authentication exists, the user id is taken from a dev-only
    header that is accepted exclusively in the development environment.
    """
    if settings.environment == "development" and x_dev_user_id:
        return x_dev_user_id
    raise HTTPException(status_code=401, detail="AUTH_REQUIRED")
