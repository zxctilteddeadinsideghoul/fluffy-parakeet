"""Unified HTTP error envelope from the data contract (section 7)."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

_CODE_MESSAGES: dict[str, str] = {
    "AUTH_REQUIRED": "Требуется вход",
    "FORBIDDEN": "Действие недоступно",
    "VERIFICATION_REQUIRED": "Требуется верификация профиля",
    "ACTIVE_PRESENCE_REQUIRED": "Требуется действующая сессия присутствия",
    "NOT_SAME_VENUE": "Участники находятся в разных заведениях",
    "INVALID_STATE_TRANSITION": "Недопустимый переход состояния",
    "REQUEST_ALREADY_EXISTS": "Повторный запрос в рамках визита запрещён",
    "OFFER_EXPIRED": "Предложение истекло",
    "MENU_ITEM_UNAVAILABLE": "Позиция недоступна",
    "RATE_LIMITED": "Превышен лимит действий",
    "PAYMENT_FAILED": "Платёжная операция не завершена",
    "NOT_FOUND": "Ресурс не найден",
    "INVALID_CURSOR": "Недопустимый курсор пагинации",
    "INVALID_CHECK_IN_TOKEN": "Чек-ин токен недействителен",
    "VALIDATION_ERROR": "Некорректные данные запроса",
    "BAD_REQUEST": "Некорректный запрос",
    "METHOD_NOT_ALLOWED": "Метод не поддерживается",
    "INTERNAL_ERROR": "Внутренняя ошибка сервера",
}

_STATUS_CODE_BY_STATUS: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "AUTH_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "INVALID_STATE_TRANSITION",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
}


def _trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", None) or "unknown"


def error_payload(
    request: Request,
    status_code: int,
    code: str,
    message: str | None = None,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "code": code,
        "message": message or _CODE_MESSAGES.get(code, code),
        "traceId": _trace_id(request),
    }
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status_code, content={"error": body})


async def starlette_http_error_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, str) and detail in _CODE_MESSAGES:
        code = detail
    elif exc.status_code >= 500:
        logger.exception(
            "http error: %s %s -> %d",
            request.method,
            request.url.path,
            exc.status_code,
        )
        return error_payload(request, exc.status_code, "INTERNAL_ERROR")
    else:
        code = _STATUS_CODE_BY_STATUS.get(exc.status_code, "BAD_REQUEST")
    return error_payload(request, exc.status_code, code)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = [
        {"loc": [str(part) for part in err.get("loc", [])], "type": err.get("type"), "msg": err.get("msg")}
        for err in exc.errors()
    ]
    logger.warning(
        "validation error: %s %s -> %s",
        request.method,
        request.url.path,
        details,
    )
    return error_payload(request, 422, "VALIDATION_ERROR")


async def unhandled_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("unhandled error: %s %s", request.method, request.url.path)
    return error_payload(request, 500, "INTERNAL_ERROR")


def register_error_handlers(app: FastAPI) -> None:
    """Register handlers that render all errors in the contract envelope."""
    app.add_exception_handler(StarletteHTTPException, starlette_http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)