"""HTTP middleware: traces every request and assigns a request trace id."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.http")


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Logs each request with its method, path, status and duration in ms."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        trace_id = uuid.uuid4().hex[:16]
        request.state.trace_id = trace_id
        start = time.perf_counter()
        method, path = request.method, request.url.path
        logger.info("request start: %s %s trace=%s", method, path, trace_id)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request failed: %s %s trace=%s", method, path, trace_id)
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request done: %s %s -> %d (%.1f ms) trace=%s",
            method,
            path,
            response.status_code,
            duration_ms,
            trace_id,
        )
        response.headers["X-Trace-Id"] = trace_id
        return response