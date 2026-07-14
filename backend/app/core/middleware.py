"""Global middleware: request ID, logging, CORS, error handling."""

import time
import uuid

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a unique request_id into every request and log entry."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])

        # Bind request_id to loguru context
        with logger.contextualize(request_id=request_id):
            start = time.perf_counter()
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start) * 1000

            logger.info(
                f"{request.method} {request.url.path} → {response.status_code}",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round(elapsed_ms, 2),
            )
            response.headers["X-Request-ID"] = request_id
            return response


async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all exceptions, return consistent error format."""

    if isinstance(exc, AppError):
        logger.warning(
            f"App error: {exc.code} — {exc.message}",
            error_code=exc.code,
            detail=exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "title": exc.code,
                "status": exc.status_code,
                "detail": exc.message,
                "errors": exc.detail.get("errors"),
                "request_id": request.headers.get("X-Request-ID", "unknown"),
            },
        )

    # Unexpected / programming error
    logger.opt(exception=exc).error("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "title": "INTERNAL_ERROR",
            "status": 500,
            "detail": "An unexpected error occurred.",
            "request_id": request.headers.get("X-Request-ID", "unknown"),
        },
    )


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI app in correct order."""

    # 1. Request ID (innermost — runs first on request, last on response)
    app.add_middleware(RequestIDMiddleware)

    # 2. CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
