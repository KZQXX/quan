"""Request and response schemas for the public API."""

from datetime import date
from datetime import datetime

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
    recorded_at: datetime | None = None
    notes: str | None = None


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


class RecordResponse(ORMModel):
    id: str
    pet_id: str
    recorded_at: datetime
    notes: str | None
