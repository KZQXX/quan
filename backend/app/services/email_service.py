"""Email notification service — SMTP skeleton."""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Send email notifications via SMTP."""

    async def send(self, to_email: str, subject: str, body: str) -> bool:
        if not settings.smtp_host:
            logger.info("SMTP not configured — logging: to=%s subject=%s", to_email, subject)
            return False
        logger.info("Email queued: to=%s subject=%s", to_email, subject)
        return False


email_service = EmailService()
