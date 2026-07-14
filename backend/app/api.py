"""Authenticated REST endpoints for the Pet Tracker MVP."""

import csv
import io
from datetime import UTC
from datetime import date
from datetime import datetime
from typing import Annotated
from typing import Any
from typing import TypeVar

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from pydantic import AwareDatetime
from sqlalchemy import Select
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.core.errors import NotFoundError
from app.core.errors import UnauthorizedError
from app.core.security import create_access_token
from app.core.security import decode_access_token
from app.core.security import hash_password
from app.core.security import verify_password
from app.models.daily_stats import DailyStats
from app.models.notification import Notification
from app.models.pet import Pet
from app.models.record import BehaviorRecord
from app.models.record import ExcretionRecord
from app.models.record import FeedingRecord
from app.models.reminder import Reminder
from app.models.user import User
from app.schemas import BehaviorCreate
from app.schemas import BehaviorRecordResponse
from app.schemas import BehaviorUpdate
from app.schemas import DailyStatsResponse
from app.schemas import DashboardResponse
from app.schemas import ExcretionCreate
from app.schemas import ExcretionRecordResponse
from app.schemas import ExcretionUpdate
from app.schemas import FeedingCreate
from app.schemas import FeedingRecordResponse
from app.schemas import FeedingUpdate
from app.schemas import LoginRequest
from app.schemas import NotificationPreferenceUpdate
from app.schemas import NotificationResponse
from app.schemas import PasswordChangeRequest
from app.schemas import PetCreate
from app.schemas import PetResponse
from app.schemas import PetUpdate
from app.schemas import RegisterRequest
from app.schemas import ReminderCreate
from app.schemas import ReminderResponse
from app.schemas import ReminderUpdate
from app.schemas import TokenResponse
from app.schemas import UserResponse
from app.services.stats_service import aggregate_daily_stats
from app.services.stats_service import get_daily_stats
from app.shared.database import get_db

router = APIRouter(prefix="/api")
DB = Annotated[AsyncSession, Depends(get_db)]
bearer_scheme = HTTPBearer(auto_error=False)
RecordModel = TypeVar("RecordModel", FeedingRecord, ExcretionRecord, BehaviorRecord)


async def current_user(
    db: DB, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
) -> User:
    if credentials is None:
        raise UnauthorizedError()
    user_id = decode_access_token(credentials.credentials)
    user = await db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("Account no longer exists")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
async def register(payload: RegisterRequest, db: DB) -> User:
    existing = await db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if existing:
        raise ConflictError("An account with this email already exists")
    user = User(
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name.strip(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(payload: LoginRequest, db: DB) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Incorrect email or password")
    return TokenResponse(
        access_token=create_access_token(user.id), user=UserResponse.model_validate(user)
    )


@router.get("/auth/me", response_model=UserResponse, tags=["Auth"])
async def get_current_user(user: CurrentUser) -> User:
    return user


@router.post("/auth/change-password", status_code=status.HTTP_204_NO_CONTENT, tags=["Auth"])
async def change_password(payload: PasswordChangeRequest, user: CurrentUser, db: DB) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    await db.commit()


async def owned_pet(pet_id: str, user: User, db: AsyncSession) -> Pet:
    pet = await db.scalar(select(Pet).where(Pet.id == pet_id, Pet.user_id == user.id))
    if pet is None:
        raise NotFoundError("Pet", pet_id)
    return pet


@router.get("/pets", response_model=list[PetResponse], tags=["Pets"])
async def list_pets(user: CurrentUser, db: DB) -> list[Pet]:
    return list(
        await db.scalars(select(Pet).where(Pet.user_id == user.id).order_by(Pet.created_at.desc()))
    )


@router.post(
    "/pets", response_model=PetResponse, status_code=status.HTTP_201_CREATED, tags=["Pets"]
)
async def create_pet(payload: PetCreate, user: CurrentUser, db: DB) -> Pet:
    pet = Pet(user_id=user.id, **payload.model_dump())
    db.add(pet)
    await db.commit()
    await db.refresh(pet)
    return pet


@router.get("/pets/{pet_id}", response_model=PetResponse, tags=["Pets"])
async def get_pet(pet_id: str, user: CurrentUser, db: DB) -> Pet:
    return await owned_pet(pet_id, user, db)


@router.patch("/pets/{pet_id}", response_model=PetResponse, tags=["Pets"])
async def update_pet(pet_id: str, payload: PetUpdate, user: CurrentUser, db: DB) -> Pet:
    pet = await owned_pet(pet_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pet, field, value)
    await db.commit()
    await db.refresh(pet)
    return pet


@router.delete("/pets/{pet_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Pets"])
async def delete_pet(pet_id: str, user: CurrentUser, db: DB) -> None:
    pet = await owned_pet(pet_id, user, db)
    await db.delete(pet)
    await db.commit()


async def create_record(
    model: type[RecordModel], pet_id: str, payload: Any, user: User, db: AsyncSession
) -> RecordModel:
    await owned_pet(pet_id, user, db)
    values = payload.model_dump(exclude_none=True)
    recorded_at = values.get("recorded_at", datetime.now(UTC))
    # Ensure tz-aware: SQLite strips timezone on round-trip
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=UTC)
    values["recorded_at"] = recorded_at
    record = model(pet_id=pet_id, **values)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    # Re-apply tzinfo after SQLite round-trip
    if record.recorded_at.tzinfo is None:
        record.recorded_at = record.recorded_at.replace(tzinfo=UTC)
    return record


async def list_records(
    model: type[RecordModel],
    pet_id: str,
    user: User,
    db: AsyncSession,
    start_date: AwareDatetime | None = None,
    end_date: AwareDatetime | None = None,
) -> list[RecordModel]:
    await owned_pet(pet_id, user, db)
    conditions = [model.pet_id == pet_id]
    if start_date:
        conditions.append(model.recorded_at >= start_date)
    if end_date:
        conditions.append(model.recorded_at <= end_date)
    query: Select[tuple[RecordModel]] = (
        select(model).where(*conditions).order_by(model.recorded_at.desc())
    )
    records = list(await db.scalars(query))
    # Re-apply tzinfo after SQLite round-trip
    for r in records:
        if r.recorded_at.tzinfo is None:
            r.recorded_at = r.recorded_at.replace(tzinfo=UTC)
    return records


async def owned_record(
    pet_id: str, record_id: str, user: User, db: AsyncSession, model: type[RecordModel]
) -> RecordModel:
    await owned_pet(pet_id, user, db)
    record = await db.get(model, record_id)
    if record is None or record.pet_id != pet_id:
        raise NotFoundError(model.__name__, record_id)
    # Re-apply tzinfo after SQLite round-trip
    if record.recorded_at.tzinfo is None:
        record.recorded_at = record.recorded_at.replace(tzinfo=UTC)
    return record


async def update_record(
    pet_id: str,
    record_id: str,
    payload: Any,
    user: User,
    db: AsyncSession,
    model: type[RecordModel],
) -> RecordModel:
    record = await owned_record(pet_id, record_id, user, db, model)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    # Re-apply tzinfo after SQLite round-trip
    if record.recorded_at.tzinfo is None:
        record.recorded_at = record.recorded_at.replace(tzinfo=UTC)
    return record


# ── Feeding Records ──────────────────────────────────────────────────────────


@router.get(
    "/pets/{pet_id}/feedings", response_model=list[FeedingRecordResponse], tags=["Feedings"]
)
async def list_feedings(
    pet_id: str,
    user: CurrentUser,
    db: DB,
    start_date: Annotated[AwareDatetime | None, Query()] = None,
    end_date: Annotated[AwareDatetime | None, Query()] = None,
) -> list[FeedingRecord]:
    return await list_records(FeedingRecord, pet_id, user, db, start_date, end_date)


@router.post(
    "/pets/{pet_id}/feedings",
    status_code=status.HTTP_201_CREATED,
    response_model=FeedingRecordResponse,
    tags=["Feedings"],
)
async def create_feeding(
    pet_id: str, payload: FeedingCreate, user: CurrentUser, db: DB
) -> FeedingRecord:
    return await create_record(FeedingRecord, pet_id, payload, user, db)


@router.get(
    "/pets/{pet_id}/feedings/{record_id}", response_model=FeedingRecordResponse, tags=["Feedings"]
)
async def get_feeding(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> FeedingRecord:
    return await owned_record(pet_id, record_id, user, db, FeedingRecord)


@router.patch(
    "/pets/{pet_id}/feedings/{record_id}", response_model=FeedingRecordResponse, tags=["Feedings"]
)
async def update_feeding(
    pet_id: str, record_id: str, payload: FeedingUpdate, user: CurrentUser, db: DB
) -> FeedingRecord:
    return await update_record(pet_id, record_id, payload, user, db, FeedingRecord)


@router.delete(
    "/pets/{pet_id}/feedings/{record_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Feedings"]
)
async def delete_feeding(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> None:
    record = await owned_record(pet_id, record_id, user, db, FeedingRecord)
    await db.delete(record)
    await db.commit()


# ── Excretion Records ────────────────────────────────────────────────────────


@router.get(
    "/pets/{pet_id}/excretions", response_model=list[ExcretionRecordResponse], tags=["Excretions"]
)
async def list_excretions(
    pet_id: str,
    user: CurrentUser,
    db: DB,
    start_date: Annotated[AwareDatetime | None, Query()] = None,
    end_date: Annotated[AwareDatetime | None, Query()] = None,
) -> list[ExcretionRecord]:
    return await list_records(ExcretionRecord, pet_id, user, db, start_date, end_date)


@router.post(
    "/pets/{pet_id}/excretions",
    status_code=status.HTTP_201_CREATED,
    response_model=ExcretionRecordResponse,
    tags=["Excretions"],
)
async def create_excretion(
    pet_id: str, payload: ExcretionCreate, user: CurrentUser, db: DB
) -> ExcretionRecord:
    return await create_record(ExcretionRecord, pet_id, payload, user, db)


@router.get(
    "/pets/{pet_id}/excretions/{record_id}",
    response_model=ExcretionRecordResponse,
    tags=["Excretions"],
)
async def get_excretion(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> ExcretionRecord:
    return await owned_record(pet_id, record_id, user, db, ExcretionRecord)


@router.patch(
    "/pets/{pet_id}/excretions/{record_id}",
    response_model=ExcretionRecordResponse,
    tags=["Excretions"],
)
async def update_excretion(
    pet_id: str, record_id: str, payload: ExcretionUpdate, user: CurrentUser, db: DB
) -> ExcretionRecord:
    return await update_record(pet_id, record_id, payload, user, db, ExcretionRecord)


@router.delete(
    "/pets/{pet_id}/excretions/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Excretions"],
)
async def delete_excretion(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> None:
    record = await owned_record(pet_id, record_id, user, db, ExcretionRecord)
    await db.delete(record)
    await db.commit()


# ── Behavior Records ─────────────────────────────────────────────────────────


@router.get(
    "/pets/{pet_id}/behaviors", response_model=list[BehaviorRecordResponse], tags=["Behaviors"]
)
async def list_behaviors(
    pet_id: str,
    user: CurrentUser,
    db: DB,
    start_date: Annotated[AwareDatetime | None, Query()] = None,
    end_date: Annotated[AwareDatetime | None, Query()] = None,
) -> list[BehaviorRecord]:
    return await list_records(BehaviorRecord, pet_id, user, db, start_date, end_date)


@router.post(
    "/pets/{pet_id}/behaviors",
    status_code=status.HTTP_201_CREATED,
    response_model=BehaviorRecordResponse,
    tags=["Behaviors"],
)
async def create_behavior(
    pet_id: str, payload: BehaviorCreate, user: CurrentUser, db: DB
) -> BehaviorRecord:
    return await create_record(BehaviorRecord, pet_id, payload, user, db)


@router.get(
    "/pets/{pet_id}/behaviors/{record_id}",
    response_model=BehaviorRecordResponse,
    tags=["Behaviors"],
)
async def get_behavior(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> BehaviorRecord:
    return await owned_record(pet_id, record_id, user, db, BehaviorRecord)


@router.patch(
    "/pets/{pet_id}/behaviors/{record_id}",
    response_model=BehaviorRecordResponse,
    tags=["Behaviors"],
)
async def update_behavior(
    pet_id: str, record_id: str, payload: BehaviorUpdate, user: CurrentUser, db: DB
) -> BehaviorRecord:
    return await update_record(pet_id, record_id, payload, user, db, BehaviorRecord)


@router.delete(
    "/pets/{pet_id}/behaviors/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Behaviors"],
)
async def delete_behavior(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> None:
    record = await owned_record(pet_id, record_id, user, db, BehaviorRecord)
    await db.delete(record)
    await db.commit()


@router.get("/dashboard", response_model=DashboardResponse, tags=["Dashboard"])
async def dashboard(user: CurrentUser, db: DB) -> dict[str, Any]:
    pet_ids = select(Pet.id).where(Pet.user_id == user.id)

    async def count(model: type[RecordModel]) -> int:
        return int(
            await db.scalar(
                select(func.count()).select_from(model).where(model.pet_id.in_(pet_ids))
            )
            or 0
        )

    # Fetch today's aggregated stats
    today_str = date.today().isoformat()
    today_stats = await get_daily_stats(db, user.id, start_date=today_str, end_date=today_str)

    # Count active reminders and unread notifications
    reminder_count = int(
        await db.scalar(
            select(func.count()).select_from(Reminder).where(
                Reminder.user_id == user.id, Reminder.enabled == True  # noqa: E712
            )
        )
        or 0
    )
    unread_count_val = int(
        await db.scalar(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == user.id,
                Notification.is_read == False,  # noqa: E712
            )
        )
        or 0
    )

    return {
        "pets": int(
            await db.scalar(select(func.count()).select_from(Pet).where(Pet.user_id == user.id))
            or 0
        ),
        "feedings": await count(FeedingRecord),
        "excretions": await count(ExcretionRecord),
        "behaviors": await count(BehaviorRecord),
        "reminders": reminder_count,
        "unread_notifications": unread_count_val,
        "today_stats": today_stats,
    }


# ── Reminders ─────────────────────────────────────────────────────────────


@router.get("/reminders", response_model=list[ReminderResponse], tags=["Reminders"])
async def list_reminders(user: CurrentUser, db: DB) -> list[Reminder]:
    result = await db.execute(
        select(Reminder)
        .where(Reminder.user_id == user.id)
        .order_by(Reminder.scheduled_time)
    )
    return list(result.scalars().all())


@router.post(
    "/reminders",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Reminders"],
)
async def create_reminder(
    payload: ReminderCreate, user: CurrentUser, db: DB
) -> Reminder:
    # If pet_id is provided, verify ownership
    if payload.pet_id:
        await owned_pet(payload.pet_id, user, db)
    reminder = Reminder(user_id=user.id, **payload.model_dump())
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return reminder


@router.get("/reminders/{reminder_id}", response_model=ReminderResponse, tags=["Reminders"])
async def get_reminder(reminder_id: str, user: CurrentUser, db: DB) -> Reminder:
    reminder = await db.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != user.id:
        raise NotFoundError("Reminder", reminder_id)
    return reminder


@router.patch("/reminders/{reminder_id}", response_model=ReminderResponse, tags=["Reminders"])
async def update_reminder(
    reminder_id: str, payload: ReminderUpdate, user: CurrentUser, db: DB
) -> Reminder:
    reminder = await db.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != user.id:
        raise NotFoundError("Reminder", reminder_id)
    if payload.pet_id and payload.pet_id != reminder.pet_id:
        await owned_pet(payload.pet_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(reminder, field, value)
    await db.commit()
    await db.refresh(reminder)
    return reminder


@router.delete(
    "/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Reminders"]
)
async def delete_reminder(reminder_id: str, user: CurrentUser, db: DB) -> None:
    reminder = await db.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != user.id:
        raise NotFoundError("Reminder", reminder_id)
    await db.delete(reminder)
    await db.commit()


# ── Notifications ─────────────────────────────────────────────────────────


@router.get("/notifications", response_model=list[NotificationResponse], tags=["Notifications"])
async def list_notifications(
    user: CurrentUser,
    db: DB,
    unread_only: Annotated[bool, Query()] = False,
) -> list[Notification]:
    conditions = [Notification.user_id == user.id]
    if unread_only:
        conditions.append(Notification.is_read == False)  # noqa: E712
    result = await db.execute(
        select(Notification)
        .where(*conditions)
        .order_by(Notification.created_at_ts.desc())
        .limit(50)
    )
    return list(result.scalars().all())


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    tags=["Notifications"],
)
async def mark_notification_read(
    notification_id: str, user: CurrentUser, db: DB
) -> Notification:
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise NotFoundError("Notification", notification_id)
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification


@router.post(
    "/notifications/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Notifications"],
)
async def mark_all_read(user: CurrentUser, db: DB) -> None:
    from sqlalchemy import update

    await db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    await db.commit()


@router.get(
    "/notifications/unread-count",
    tags=["Notifications"],
)
async def unread_count(user: CurrentUser, db: DB) -> dict[str, int]:
    count = await db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user.id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    return {"unread": int(count or 0)}


# ── Notification Preferences ──────────────────────────────────────────────


@router.patch("/auth/preferences", response_model=UserResponse, tags=["Auth"])
async def update_notification_preferences(
    payload: NotificationPreferenceUpdate, user: CurrentUser, db: DB
) -> User:
    if payload.notify_email is not None:
        user.notify_email = payload.notify_email
    if payload.webhook_url is not None:
        user.webhook_url = payload.webhook_url if payload.webhook_url else None
    await db.commit()
    await db.refresh(user)
    return user


# ── Statistics ─────────────────────────────────────────────────────────────


@router.get("/stats/daily", response_model=list[DailyStatsResponse], tags=["Statistics"])
async def daily_stats(
    user: CurrentUser,
    db: DB,
    pet_id: Annotated[str | None, Query()] = None,
    start_date: Annotated[str | None, Query()] = None,
    end_date: Annotated[str | None, Query()] = None,
) -> list[DailyStats]:
    return await get_daily_stats(db, user.id, pet_id=pet_id, start_date=start_date, end_date=end_date)


@router.post("/stats/aggregate", tags=["Statistics"])
async def trigger_aggregation(
    user: CurrentUser,
    db: DB,
    target_date: Annotated[str | None, Query()] = None,
) -> dict[str, Any]:
    """Manually trigger daily stats aggregation (defaults to today)."""
    parsed_date = date.fromisoformat(target_date) if target_date else date.today()
    count = await aggregate_daily_stats(db, target_date=parsed_date)
    return {"aggregated": count, "date": parsed_date.isoformat()}


@router.get("/stats/report", tags=["Statistics"])
async def stats_report(
    user: CurrentUser,
    db: DB,
    pet_id: Annotated[str | None, Query()] = None,
    start_date: Annotated[str | None, Query()] = None,
    end_date: Annotated[str | None, Query()] = None,
) -> dict[str, Any]:
    """Return aggregated report data for the given date range."""
    stats = await get_daily_stats(
        db, user.id, pet_id=pet_id, start_date=start_date, end_date=end_date,
    )

    # Fetch pet names for display
    pet_ids = list({s.pet_id for s in stats})
    pet_map: dict[str, str] = {}
    if pet_ids:
        rows = (await db.execute(
            select(Pet.id, Pet.name).where(Pet.id.in_(pet_ids))
        )).all()
        pet_map = {r[0]: r[1] for r in rows}

    # Aggregate totals
    totals = {"feeding_count": 0, "excretion_count": 0, "behavior_count": 0, "total_duration_minutes": 0}
    days = len(stats)
    per_pet: dict[str, dict] = {}
    for s in stats:
        totals["feeding_count"] += s.feeding_count
        totals["excretion_count"] += s.excretion_count
        totals["behavior_count"] += s.behavior_count
        totals["total_duration_minutes"] += s.total_duration_minutes
        pid = s.pet_id
        if pid not in per_pet:
            per_pet[pid] = {
                "pet_id": pid,
                "pet_name": pet_map.get(pid, "Unknown"),
                "feeding_count": 0,
                "excretion_count": 0,
                "behavior_count": 0,
                "total_duration_minutes": 0,
                "days_tracked": 0,
            }
        p = per_pet[pid]
        p["feeding_count"] += s.feeding_count
        p["excretion_count"] += s.excretion_count
        p["behavior_count"] += s.behavior_count
        p["total_duration_minutes"] += s.total_duration_minutes
        p["days_tracked"] += 1

    return {
        "date_range": {"start": start_date, "end": end_date},
        "days": days,
        "totals": totals,
        "per_pet": sorted(per_pet.values(), key=lambda x: x["pet_name"]),
    }


@router.get("/stats/export", tags=["Statistics"])
async def export_csv(
    user: CurrentUser,
    db: DB,
    pet_id: Annotated[str | None, Query()] = None,
    start_date: Annotated[str | None, Query()] = None,
    end_date: Annotated[str | None, Query()] = None,
) -> StreamingResponse:
    """Export daily stats as CSV file."""
    stats = await get_daily_stats(
        db, user.id, pet_id=pet_id, start_date=start_date, end_date=end_date,
    )

    # Fetch pet names
    pet_ids = list({s.pet_id for s in stats})
    pet_map: dict[str, str] = {}
    if pet_ids:
        rows = (await db.execute(
            select(Pet.id, Pet.name).where(Pet.id.in_(pet_ids))
        )).all()
        pet_map = {r[0]: r[1] for r in rows}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "宠物", "喂食次数", "排便次数", "行为次数", "行为总时长(分钟)"])
    for s in stats:
        writer.writerow([
            s.date,
            pet_map.get(s.pet_id, s.pet_id),
            s.feeding_count,
            s.excretion_count,
            s.behavior_count,
            s.total_duration_minutes,
        ])

    output.seek(0)
    filename = f"pet_stats_{start_date or 'all'}_{end_date or 'all'}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
