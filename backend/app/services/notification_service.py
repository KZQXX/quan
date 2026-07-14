"""Notification service — bridge between reminders and delivery channels.

Processes due reminders, creates in-app notifications, and dispatches
to configured channels (email, webhook).
"""

import logging
from datetime import UTC
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.reminder import Reminder
from app.models.user import User
from app.services.email_service import email_service
from app.services.webhook_service import webhook_service

logger = logging.getLogger(__name__)

_REPEAT_DAYS: dict[str, int | None] = {
    "none": None,
    "daily": 1,
    "weekly": 7,
}


def _parse_time(time_str: str) -> tuple[int, int]:
    """Parse HH:MM into (hour, minute)."""
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])


async def process_due_reminders(db: AsyncSession) -> int:
    """Check all enabled reminders and trigger notifications for due ones.

    Returns the number of reminders processed.
    """
    now = datetime.now(UTC)
    today = now.date()
    current_hour = now.hour
    current_minute = now.minute
    today_iso = today.isoformat()

    result = await db.execute(
        select(Reminder).where(Reminder.enabled == True)  # noqa: E712
    )
    reminders = result.scalars().all()

    processed = 0
    for reminder in reminders:
        # Skip if already triggered today
        if reminder.last_triggered_at == today_iso:
            continue

        scheduled_hour, scheduled_minute = _parse_time(reminder.scheduled_time)

        # Check if it's time to trigger (within the current minute window)
        if scheduled_hour != current_hour or scheduled_minute != current_minute:
            continue

        # Check repeat rule — skip "none" after first trigger
        if reminder.repeat_rule == "none" and reminder.last_triggered_at is not None:
            continue

        # Weekly — check day of week
        if reminder.repeat_rule == "weekly":
            if not reminder.cron_expression:
                continue
            # cron_expression stores day-of-week: "mon", "tue", etc.
            dow_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
            target_dow = dow_map.get(reminder.cron_expression.lower(), -1)
            if today.weekday() != target_dow:
                continue

        # Trigger notification
        user = await db.get(User, reminder.user_id)
        if user is None:
            continue

        pet_name = ""
        if reminder.pet_id:
            from app.models.pet import Pet
            pet = await db.get(Pet, reminder.pet_id)
            if pet:
                pet_name = f" ({pet.name})"

        title = f"提醒：{reminder.title}"
        message = f"{reminder.title}{pet_name} — 该执行啦！"

        notification = Notification(
            user_id=reminder.user_id,
            type="reminder",
            title=title,
            message=message,
            is_read=False,
            created_at_ts=now.isoformat(),
        )
        db.add(notification)
        processed += 1

        # Dispatch to external channels
        if user.notify_email:
            await email_service.send(
                to_email=user.email,
                subject=title,
                body=message,
            )

        if user.webhook_url:
            await webhook_service.push(
                url=user.webhook_url,
                payload={"title": title, "message": message, "timestamp": now.isoformat()},
            )

        # Mark as triggered
        reminder.last_triggered_at = today_iso

    if reminders:
        await db.commit()

    return processed
