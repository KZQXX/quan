"""Reminder scheduler — APScheduler powered periodic checks.

Runs an AsyncIOScheduler that calls process_due_reminders every minute.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.services.notification_service import process_due_reminders
from app.services.stats_service import aggregate_daily_stats
from app.shared.database import async_session_factory

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Manages the APScheduler instance for reminder triggering."""

    def __init__(self) -> None:
        self.scheduler: AsyncIOScheduler | None = None

    async def start(self) -> None:
        """Start the scheduler if enabled in config."""
        if not settings.scheduler_enabled:
            logger.info("Scheduler disabled via config — skipping start")
            return

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(
            self._check_reminders,
            "interval",
            minutes=1,
            id="check_reminders",
            replace_existing=True,
            coalesce=True,  # skip missed runs
            max_instances=1,
        )
        # Daily stats aggregation at 00:05 UTC
        self.scheduler.add_job(
            self._aggregate_stats,
            "cron",
            hour=0,
            minute=5,
            id="aggregate_daily_stats",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        self.scheduler.start()
        logger.info("APScheduler started — checking reminders every 1 min, daily stats at 00:05 UTC")

    async def shutdown(self) -> None:
        """Gracefully shut down the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            logger.info("APScheduler shut down")

    async def _check_reminders(self) -> None:
        """Check for due reminders and create notifications."""
        try:
            async with async_session_factory() as session:
                processed = await process_due_reminders(session)
                if processed:
                    logger.info("Reminder check: %d notifications created", processed)
        except Exception:
            logger.exception("Reminder check failed")

    async def _aggregate_stats(self) -> None:
        """Aggregate daily stats for all pets (runs at midnight)."""
        from datetime import date
        from datetime import timedelta

        try:
            yesterday = date.today() - timedelta(days=1)
            async with async_session_factory() as session:
                count = await aggregate_daily_stats(session, target_date=yesterday)
                logger.info("Daily stats aggregated: %d pet(s) for %s", count, yesterday.isoformat())
        except Exception:
            logger.exception("Daily stats aggregation failed")


reminder_scheduler = ReminderScheduler()
