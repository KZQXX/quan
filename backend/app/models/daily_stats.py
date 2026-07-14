"""DailyStats model — pre-aggregated daily pet statistics."""

from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database import Base
from app.shared.models import TimestampMixin
from app.shared.models import UUIDMixin


class DailyStats(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "daily_stats"
    __table_args__ = (
        Index("ix_daily_stats_date_user", "date", "user_id"),
        Index("ix_daily_stats_pet_date", "pet_id", "date", unique=True),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pet_id: Mapped[str] = mapped_column(
        ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # YYYY-MM-DD date string
    feeding_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    excretion_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    behavior_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_duration_minutes: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # sum of behavior duration_minutes

    def __repr__(self) -> str:
        return f"<DailyStats {self.pet_id} on {self.date}>"
