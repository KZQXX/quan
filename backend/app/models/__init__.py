"""All SQLAlchemy models — import here so Alembic can discover them."""

from app.models.daily_stats import DailyStats
from app.models.notification import Notification
from app.models.pet import Pet
from app.models.record import BehaviorRecord
from app.models.record import ExcretionRecord
from app.models.record import FeedingRecord
from app.models.reminder import Reminder
from app.models.user import User

__all__ = [
    "BehaviorRecord",
    "DailyStats",
    "ExcretionRecord",
    "FeedingRecord",
    "Notification",
    "Pet",
    "Reminder",
    "User",
]
