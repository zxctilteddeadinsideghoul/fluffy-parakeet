"""Application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware import RequestTracingMiddleware
from app.containers.container import Container
from app.core.config import settings
from app.core.db import Base, engine
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.routes import dependencies as route_dependencies
from app.routes.auth import router as auth_router
from app.routes.drink import router as drink_router
from app.routes.health import router as health_router
from app.routes.presence import router as presence_router
from app.routes.profile import router as profile_router

logger = logging.getLogger("app.main")
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        app.container.photo_storage().ensure_bucket()  # type: ignore[attr-defined]
    except Exception:
        logger.exception("photo storage bucket setup failed")
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(RequestTracingMiddleware)
register_error_handlers(app)

container = Container()
container.wire(modules=[route_dependencies])
app.container = container  # type: ignore[attr-defined]

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(presence_router)
app.include_router(profile_router)
app.include_router(drink_router)