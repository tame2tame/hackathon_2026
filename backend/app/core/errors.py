"""Ошибки API в формате problem+json (RFC 9457) с кодами из каталога ARCHITECTURE.md, раздел 5."""

import logging
import uuid
from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("radar.errors")

PROBLEM_MEDIA_TYPE = "application/problem+json"


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    INTERACTION_VERSION_CONFLICT = "INTERACTION_VERSION_CONFLICT"
    WF_TRANSITION_NOT_ALLOWED = "WF_TRANSITION_NOT_ALLOWED"
    WF_COMMENT_REQUIRED = "WF_COMMENT_REQUIRED"
    WF_ATTACHMENT_REQUIRED = "WF_ATTACHMENT_REQUIRED"
    FILE_TYPE_NOT_ALLOWED = "FILE_TYPE_NOT_ALLOWED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    IMPORT_MAPPING_INVALID = "IMPORT_MAPPING_INVALID"
    REPORT_TOO_LARGE = "REPORT_TOO_LARGE"
    INTEGRATION_UNAVAILABLE = "INTEGRATION_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


_CATALOG: dict[ErrorCode, tuple[int, str]] = {
    ErrorCode.VALIDATION_ERROR: (422, "Неверные параметры запроса"),
    ErrorCode.AUTH_REQUIRED: (401, "Нужна авторизация"),
    ErrorCode.AUTH_FORBIDDEN: (403, "Недостаточно прав"),
    ErrorCode.NOT_FOUND: (404, "Не найдено"),
    ErrorCode.INTERACTION_VERSION_CONFLICT: (409, "Запись уже изменена"),
    ErrorCode.WF_TRANSITION_NOT_ALLOWED: (409, "Переход недоступен"),
    ErrorCode.WF_COMMENT_REQUIRED: (422, "Нужен комментарий"),
    ErrorCode.WF_ATTACHMENT_REQUIRED: (422, "Нужен документ"),
    ErrorCode.FILE_TYPE_NOT_ALLOWED: (415, "Тип файла не поддерживается"),
    ErrorCode.FILE_TOO_LARGE: (413, "Файл слишком большой"),
    ErrorCode.IMPORT_MAPPING_INVALID: (422, "Маппинг колонок неполный"),
    ErrorCode.REPORT_TOO_LARGE: (422, "Отчёт слишком большой"),
    ErrorCode.INTEGRATION_UNAVAILABLE: (502, "Внешняя система недоступна"),
    ErrorCode.INTERNAL_ERROR: (500, "Внутренняя ошибка"),
}


class FieldError(BaseModel):
    field: str
    message: str


class Problem(BaseModel):
    """Тело ответа с ошибкой."""

    type: str = "about:blank"
    title: str
    status: int
    code: ErrorCode
    detail: str | None = None
    trace_id: str
    errors: list[FieldError] = []


class AppError(Exception):
    """Ожидаемая ошибка бизнес-логики с кодом из каталога."""

    def __init__(
        self,
        code: ErrorCode,
        detail: str | None = None,
        *,
        errors: list[FieldError] | None = None,
    ) -> None:
        super().__init__(detail or code.value)
        self.code = code
        self.detail = detail
        self.errors = errors or []

    @property
    def status(self) -> int:
        return _CATALOG[self.code][0]


def error_responses(*codes: ErrorCode) -> dict[int | str, dict[str, Any]]:
    """Ответы с ошибками для OpenAPI: один ответ на статус со списком своих кодов."""
    by_status: dict[int, list[str]] = {}
    for code in codes:
        by_status.setdefault(_CATALOG[code][0], []).append(code.value)
    return {
        status: {"model": Problem, "description": " · ".join(values)}
        for status, values in by_status.items()
    }


class TraceIdMiddleware:
    """Присваивает каждому запросу trace_id и возвращает его в заголовке X-Trace-Id."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        trace_id = uuid.uuid4().hex[:16]
        scope.setdefault("state", {})["trace_id"] = trace_id

        async def send_with_trace(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message).append("X-Trace-Id", trace_id)
            await send(message)

        await self.app(scope, receive, send_with_trace)


def _trace_id(request: Request) -> str:
    return str(getattr(request.state, "trace_id", "") or uuid.uuid4().hex[:16])


def problem_response(
    request: Request,
    code: ErrorCode,
    detail: str | None = None,
    *,
    errors: list[FieldError] | None = None,
    status: int | None = None,
) -> JSONResponse:
    default_status, title = _CATALOG[code]
    body = Problem(
        title=title,
        status=status or default_status,
        code=code,
        detail=detail,
        trace_id=_trace_id(request),
        errors=errors or [],
    )
    return JSONResponse(
        body.model_dump(mode="json"), status_code=body.status, media_type=PROBLEM_MEDIA_TYPE
    )


_HTTP_STATUS_CODES = {
    401: ErrorCode.AUTH_REQUIRED,
    403: ErrorCode.AUTH_FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
}


def install_error_handlers(app: FastAPI) -> None:
    async def on_app_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, AppError)  # noqa: S101 — зарегистрирован только для AppError
        return problem_response(request, exc.code, exc.detail, errors=exc.errors)

    async def on_validation_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, RequestValidationError)  # noqa: S101
        errors = [
            FieldError(
                field=".".join(
                    str(part) for part in err["loc"] if part not in {"body", "query", "path"}
                ),
                message=str(err["msg"]),
            )
            for err in exc.errors()
        ]
        return problem_response(request, ErrorCode.VALIDATION_ERROR, errors=errors)

    async def on_http_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, StarletteHTTPException)  # noqa: S101
        if exc.status_code >= 500:
            return problem_response(request, ErrorCode.INTERNAL_ERROR, status=exc.status_code)
        code = _HTTP_STATUS_CODES.get(exc.status_code, ErrorCode.VALIDATION_ERROR)
        return problem_response(request, code, str(exc.detail), status=exc.status_code)

    async def on_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Стек уходит только в журнал; клиент получает trace_id для поиска записи.
        logger.exception("Необработанная ошибка, trace_id=%s", _trace_id(request), exc_info=exc)
        return problem_response(request, ErrorCode.INTERNAL_ERROR)

    app.add_exception_handler(AppError, on_app_error)
    app.add_exception_handler(RequestValidationError, on_validation_error)
    app.add_exception_handler(StarletteHTTPException, on_http_error)
    app.add_exception_handler(Exception, on_unexpected_error)
