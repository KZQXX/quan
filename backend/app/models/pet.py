"""Pet model — pet profile and basic info."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database import Base
from app.shared.models import TimestampMixin, UUIDMixin


class Pet(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "pets"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    species: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )  # e.g. "犬", "猫"
    breed: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # e.g. "金毛", "英短"
    birth_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    def __repr__(self) -> str:
        return f"<Pet {self.name} ({self.species})>"
