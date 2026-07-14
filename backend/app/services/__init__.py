"""Email notification service — SMTP skeleton.

Uses app.core.config.settings for SMTP connection parameters.
Currently a skeleton; implement SMTP integration for production.
"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Send email notifications via SMTP.

    Currently implemented as a logging-only skeleton.
    To activate: configure SMTP_* env vars and uncomment SMTP send logic.
    """

    async def send(self, to_email: str, subject: str, body: str) -> bool:
        """Send an email. Returns True if successful, False otherwise.

        Skeleton: logs the email instead of sending.
        Production: use aiosmtplib or a background task queue.
        """
        if not settings.smtp_host:
            logger.info("SMTP not configured — logging email instead: to=%s subject=%s", to_email, subject)
            return False

        logger.info("Email queued: to=%s subject=%s", to_email, subject)
        # TODO: implement actual SMTP send via aiosmtplib
        # import aiosmtplib
        # message = aiosmtplib.EmailMessage(...)
        # await aiosmtplib.send(message, hostname=settings.smtp_host, port=settings.smtp_port)
        return False


email_service = EmailService()
