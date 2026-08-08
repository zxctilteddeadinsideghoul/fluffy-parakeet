"""HTTP middleware: trace every request and response to the app log."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.http")


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Logs each request with its method, path, status and duration in ms."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        method, path = request.method, request.url.path
        logger.info("request start: %s %s", method, path)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request failed: %s %s", method, path)
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request done: %s %s -> %d (%.1f ms)",
            method,
            path,
            response.status_code,
            duration_ms,
        )
        return response