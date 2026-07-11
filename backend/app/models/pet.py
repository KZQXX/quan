"""Pet model — pet profile and basic info."""

from datetime import date

from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.shared.database import Base
from app.shared.models import TimestampMixin
from app.shared.models import UUIDMixin


class Pet(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "pets"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    species: Mapped[str] = mapped_column(String(50), nullable=False, default="")  # e.g. "犬", "猫"
    breed: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "金毛", "英短"
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Pet {self.name} ({self.species})>"
