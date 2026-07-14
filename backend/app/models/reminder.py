"""Reminder model — scheduled pet-care reminders."""

from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database import Base
from app.shared.models import TimestampMixin
from app.shared.models import UUIDMixin


class Reminder(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reminders"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pet_id: Mapped[str | None] = mapped_column(
        ForeignKey("pets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    reminder_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="other"
    )  # feeding, grooming, medication, exercise, other
    scheduled_time: Mapped[str] = mapped_column(
        String(5), nullable=False
    )  # HH:MM format — time of day
    repeat_rule: Mapped[str] = mapped_column(
        String(100), nullable=False, default="none"
    )  # none, daily, weekly, custom cron
    cron_expression: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # full cron for custom schedules
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # ISO 8601 date string (YYYY-MM-DD)

    def __repr__(self) -> str:
        return f"<Reminder {self.title} ({self.reminder_type})>"
