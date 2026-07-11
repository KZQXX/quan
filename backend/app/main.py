"""FastAPI application entry point — Pet Tracker MVP."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from sqlalchemy import text

from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import logger
from app.core.logging import setup_logging
from app.core.middleware import global_error_handler
from app.core.middleware import setup_middleware
from app.shared.database import async_session_factory
from app.shared.database import engine

# ─── Lifespan (startup / shutdown) ───────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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
    await engine.dispose()


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
async def health_check() -> dict[str, str]:
    """Liveness probe — is the process alive?"""
    return {"status": "ok", "version": settings.app_version}


@app.get("/api/ready", tags=["Health"])
async def readiness_check(request: Request) -> JSONResponse:
    """Readiness probe — is the app ready to serve traffic?"""
    checks: dict[str, dict[str, str]] = {
        "app": {"status": "ok"},
    }

    # Database check
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}
        logger.error("Database health check failed", error=str(e))
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
async def root() -> Response:
    return HTMLResponse(INDEX_HTML)


INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pet Tracker · 宠物行为分析</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex; align-items: center; justify-content: center;
        }
        .card {
            background: rgba(255,255,255,0.95);
            border-radius: 24px;
            padding: 48px 40px;
            max-width: 480px; width: 90%;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }
        .emoji { font-size: 64px; margin-bottom: 16px; }
        h1 { font-size: 28px; color: #1a1a2e; margin-bottom: 8px; }
        .version { color: #999; font-size: 13px; margin-bottom: 24px; }
        .desc { color: #555; line-height: 1.7; margin-bottom: 32px; font-size: 15px; }
        .grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-bottom: 28px; }
        .tag {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #fff; padding: 6px 16px; border-radius: 20px;
            font-size: 13px; font-weight: 500;
        }
        .stack { color: #999; font-size: 12px; margin-bottom: 24px; }
        .links { display: flex; gap: 12px; justify-content: center; }
        .links a {
            text-decoration: none; color: #667eea; font-size: 14px;
            padding: 8px 20px; border: 1px solid #667eea;
            border-radius: 20px; transition: all 0.2s;
        }
        .links a:hover { background: #667eea; color: #fff; }
        .progress { margin-top: 32px; padding-top: 24px; border-top: 1px solid #eee; }
        .progress h3 { font-size: 13px; color: #999; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }
        .steps { display: flex; gap: 6px; justify-content: center; }
        .step {
            width: 28px; height: 6px; border-radius: 3px;
            background: #e0e0e0; transition: background 0.3s;
        }
        .step.done { background: linear-gradient(90deg, #667eea, #764ba2); }
    </style>
</head>
<body>
    <div class="card">
        <div class="emoji">🐾</div>
        <h1>Pet Tracker</h1>
        <div class="version">v0.1.0 · M1 脚手架</div>
        <p class="desc">
            云端多用户宠物行为分析 SaaS<br>
            记录进食、排便、行为，用数据读懂你的宠物
        </p>
        <div class="grid">
            <span class="tag">🥣 进食记录</span>
            <span class="tag">💩 排便追踪</span>
            <span class="tag">🎾 行为分析</span>
            <span class="tag">📊 仪表盘</span>
            <span class="tag">🔔 智能提醒</span>
        </div>
        <div class="stack">FastAPI + Vue 3 + SQLAlchemy</div>
        <div class="links">
            <a href="/api/health">Health</a>
            <a href="/api/docs">API 文档</a>
        </div>
        <div class="progress">
            <h3>开发进度</h3>
            <div class="steps">
                <span class="step done"></span>
                <span class="step"></span>
                <span class="step"></span>
                <span class="step"></span>
                <span class="step"></span>
            </div>
            <p style="font-size:12px;color:#bbb;margin-top:6px;">M1 D1 ✅ · D2 →</p>
        </div>
    </div>
</body>
</html>"""
