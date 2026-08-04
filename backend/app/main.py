from fastapi import FastAPI

from app.api.presence import router as presence_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(presence_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
