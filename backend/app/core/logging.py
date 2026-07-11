"""Structured JSON logging with loguru — no console.log equivalent."""

import sys

from loguru import logger

from app.core.config import settings


def _safe_request_id(record: dict) -> str:
    """Return request_id or '-' if not yet bound (e.g., during startup)."""
    result: str = record["extra"].get("request_id", "-")
    return result


def setup_logging() -> None:
    """Configure loguru for structured JSON output."""
    logger.remove()  # Remove default handler
    logger.configure(patcher=lambda r: r["extra"].setdefault("request_id", "-"))

    # Console: colorized for dev, JSON for prod
    if settings.debug:
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{extra[request_id]}</cyan> | "
                "<level>{message}</level>"
            ),
            level=settings.log_level,
            colorize=True,
        )
    else:
        logger.add(
            sys.stderr,
            format=(
                '{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}","level":"{level}",'
                '"request_id":"{extra[request_id]}","message":"{message}","module":"{module}","line":{line}}}'
            ),
            level=settings.log_level,
            serialize=False,  # loguru format handles the JSON structure above
        )

    # File: always structured JSON for persistence
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        format=(
            '{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}","level":"{level}",'
            '"request_id":"{extra[request_id]}","message":"{message}","module":"{module}","line":{line}}}'
        ),
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
    )


__all__ = ["logger", "setup_logging"]
