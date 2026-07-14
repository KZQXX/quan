"""Notification model — in-app alerts for users."""

from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database import Base
from app.shared.models import UUIDMixin


class Notification(Base, UUIDMixin):
    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="reminder"
    )  # reminder, alert, info
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at_ts: Mapped[str] = mapped_column(
        String(30), nullable=False, default=""
    )  # ISO 8601 datetime string

    def __repr__(self) -> str:
        return f"<Notification {self.title} (read={self.is_read})>"
