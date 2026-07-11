"""User model — authentication and profile."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base
from app.shared.models import TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default=""
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
