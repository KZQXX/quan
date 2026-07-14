"""Webhook notification service — push notifications to external URLs.

Currently a placeholder; implement HTTP POST delivery for production.
"""

import logging

logger = logging.getLogger(__name__)


class WebhookService:
    """Push notifications to user-configured webhook URLs."""

    async def push(self, url: str, payload: dict) -> bool:
        """Push a webhook payload. Returns True on success, False otherwise."""
        logger.info("Webhook push to %s: %s", url, payload.get("title", ""))
        # TODO: implement HTTP POST via httpx
        # async with httpx.AsyncClient() as client:
        #     resp = await client.post(url, json=payload, timeout=10)
        #     return resp.is_success
        return False


webhook_service = WebhookService()
