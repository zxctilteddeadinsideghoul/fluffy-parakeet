from fastapi import FastAPI

from app.api.middleware import RequestTracingMiddleware
from app.containers.container import Container
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.routes import dependencies as route_dependencies
from app.routes.health import router as health_router
from app.routes.presence import router as presence_router

configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(RequestTracingMiddleware)
register_error_handlers(app)

container = Container()
container.wire(modules=[route_dependencies])
app.container = container  # type: ignore[attr-defined]

app.include_router(health_router)
app.include_router(presence_router)