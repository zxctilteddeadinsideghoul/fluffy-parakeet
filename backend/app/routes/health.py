"""Health check route."""

from fastapi import APIRouter

from app.schemas.base import SuccessEnvelope

router = APIRouter(tags=["health"])


@router.get("/health", response_model=SuccessEnvelope[dict[str, str]])
async def health() -> SuccessEnvelope[dict[str, str]]:
    return SuccessEnvelope(data={"status": "ok"})