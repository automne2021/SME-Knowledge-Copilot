"""RAG error envelope {error: {code, message, details}, request_id} (spec 10)."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, details: dict | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def error_response(
    request: Request, status_code: int, code: str, message: str, details: dict | None = None
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    headers = {"Cache-Control": "no-store"}
    if request_id:
        headers["X-Request-ID"] = request_id
    if status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {"code": code, "message": message, "details": details},
            "request_id": request_id,
        },
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(request, exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        # SQL exceptions can embed bound credentials/text. Log type/ID, not parameters.
        logger.error(
            "Database error type=%s request_id=%s",
            type(exc).__name__,
            getattr(request.state, "request_id", None),
        )
        return error_response(
            request, 503, "database_unavailable", "Database tạm thời chưa sẵn sàng"
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(request, exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(request, 422, "validation_error", "Dữ liệu gửi lên không hợp lệ")

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Avoid exception text/tracebacks that may embed credentials or source text.
        logger.error(
            "Unhandled error type=%s request_id=%s",
            type(exc).__name__,
            getattr(request.state, "request_id", None),
        )
        return error_response(request, 500, "internal_error", "Lỗi hệ thống")


def success(request: Request, data) -> dict:
    return {"data": data, "request_id": request.state.request_id}
