"""Request and response schemas for the public API."""

from datetime import date
from typing import Literal

from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserResponse(ORMModel):
    id: str
    email: EmailStr
    display_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


class PetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    species: str = Field(min_length=1, max_length=50)
    breed: str | None = Field(default=None, max_length=100)
    birth_date: date | None = None
    avatar_url: str | None = None
    notes: str | None = None


class PetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    species: str | None = Field(default=None, min_length=1, max_length=50)
    breed: str | None = Field(default=None, max_length=100)
    birth_date: date | None = None
    avatar_url: str | None = None
    notes: str | None = None


class PetResponse(ORMModel):
    id: str
    name: str
    species: str
    breed: str | None
    birth_date: date | None
    avatar_url: str | None
    notes: str | None


class RecordBase(BaseModel):
    recorded_at: AwareDatetime | None = None
    notes: str | None = None
    source: Literal["manual", "quick_checkin"] = "manual"


class FeedingCreate(RecordBase):
    food_type: str = Field(min_length=1, max_length=100)
    amount: float | None = Field(default=None, ge=0)


class ExcretionCreate(RecordBase):
    type: str = Field(min_length=1, max_length=30)
    consistency: str | None = Field(default=None, max_length=30)


class BehaviorCreate(RecordBase):
    behavior_type: str = Field(min_length=1, max_length=100)
    duration_minutes: int | None = Field(default=None, ge=0)
    mood: str | None = Field(default=None, max_length=50)


class FeedingRecordResponse(ORMModel):
    id: str
    pet_id: str
    recorded_at: AwareDatetime
    food_type: str
    amount: float | None
    source: str
    notes: str | None


class FeedingUpdate(BaseModel):
    food_type: str | None = Field(default=None, min_length=1, max_length=100)
    amount: float | None = Field(default=None, ge=0)
    notes: str | None = None
    recorded_at: AwareDatetime | None = None


class ExcretionRecordResponse(ORMModel):
    id: str
    pet_id: str
    recorded_at: AwareDatetime
    source: str
    type: str
    consistency: str | None
    notes: str | None


class ExcretionUpdate(BaseModel):
    type: str | None = Field(default=None, min_length=1, max_length=30)
    consistency: str | None = Field(default=None, max_length=30)
    notes: str | None = None
    recorded_at: AwareDatetime | None = None


class BehaviorRecordResponse(ORMModel):
    id: str
    pet_id: str
    recorded_at: AwareDatetime
    source: str
    behavior_type: str
    duration_minutes: int | None
    mood: str | None
    notes: str | None


class BehaviorUpdate(BaseModel):
    behavior_type: str | None = Field(default=None, min_length=1, max_length=100)
    duration_minutes: int | None = Field(default=None, ge=0)
    mood: str | None = Field(default=None, max_length=50)
    notes: str | None = None
    recorded_at: AwareDatetime | None = None


# ── Reminder Schemas ──────────────────────────────────────────────────────


class ReminderCreate(BaseModel):
    pet_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    reminder_type: str = Field(default="other", max_length=50)
    scheduled_time: str = Field(
        pattern=r"^\d{2}:\d{2}$"
    )  # HH:MM
    repeat_rule: str = Field(default="none", max_length=100)
    cron_expression: str | None = Field(default=None, max_length=100)
    enabled: bool = True


class ReminderUpdate(BaseModel):
    pet_id: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    reminder_type: str | None = Field(default=None, max_length=50)
    scheduled_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    repeat_rule: str | None = Field(default=None, max_length=100)
    cron_expression: str | None = Field(default=None, max_length=100)
    enabled: bool | None = None


class ReminderResponse(ORMModel):
    id: str
    pet_id: str | None
    title: str
    reminder_type: str
    scheduled_time: str
    repeat_rule: str
    cron_expression: str | None
    enabled: bool
    last_triggered_at: str | None


# ── Notification Schemas ──────────────────────────────────────────────────


class NotificationResponse(ORMModel):
    id: str
    type: str
    title: str
    message: str | None
    is_read: bool
    created_at_ts: str


class NotificationPreferenceUpdate(BaseModel):
    notify_email: bool | None = None
    webhook_url: str | None = Field(default=None, max_length=500)
