"""FastAPI application entry point — Pet Tracker MVP."""

import asyncio
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import logger, setup_logging
from app.core.middleware import global_error_handler, setup_middleware


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → yield → shutdown."""

    # Startup
    setup_logging()
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version}",
        debug=settings.debug,
    )

    yield  # Application runs here

    # Shutdown (graceful)
    logger.info("Shutting down gracefully...")


# ─── FastAPI App ─────────────────────────────────────────────────────────


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Register middleware
setup_middleware(app)

# Register global error handler
app.add_exception_handler(AppError, global_error_handler)
app.add_exception_handler(Exception, global_error_handler)


# ─── Health Check Endpoints ──────────────────────────────────────────────


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Liveness probe — is the process alive?"""
    return {"status": "ok", "version": settings.app_version}


@app.get("/api/ready", tags=["Health"])
async def readiness_check(request: Request):
    """Readiness probe — is the app ready to serve traffic?"""
    # Future: check DB, Redis, etc.
    checks: dict[str, dict[str, str]] = {
        "app": {"status": "ok"},
    }
    all_ok = all(c["status"] == "ok" for c in checks.values())
    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
        },
    )


# ─── Root Redirect ───────────────────────────────────────────────────────


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/api/docs" if settings.debug else None,
    }
