"""Models for the three daily pet record types."""

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database import Base
from app.shared.models import TimestampMixin
from app.shared.models import UUIDMixin


class PetRecordMixin:
    pet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )


class FeedingRecord(Base, UUIDMixin, TimestampMixin, PetRecordMixin):
    __tablename__ = "feeding_records"
    food_type: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExcretionRecord(Base, UUIDMixin, TimestampMixin, PetRecordMixin):
    __tablename__ = "excretion_records"
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    consistency: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class BehaviorRecord(Base, UUIDMixin, TimestampMixin, PetRecordMixin):
    __tablename__ = "behavior_records"
    behavior_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mood: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
