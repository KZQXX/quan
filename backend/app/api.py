"""Authenticated REST endpoints for the Pet Tracker MVP."""

from datetime import UTC
from datetime import datetime
from typing import Annotated
from typing import Any
from typing import TypeVar

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
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
from app.models.pet import Pet
from app.models.record import BehaviorRecord
from app.models.record import ExcretionRecord
from app.models.record import FeedingRecord
from app.models.user import User
from app.schemas import BehaviorCreate
from app.schemas import BehaviorRecordResponse
from app.schemas import BehaviorUpdate
from app.schemas import ExcretionCreate
from app.schemas import ExcretionRecordResponse
from app.schemas import ExcretionUpdate
from app.schemas import FeedingCreate
from app.schemas import FeedingRecordResponse
from app.schemas import FeedingUpdate
from app.schemas import LoginRequest
from app.schemas import PasswordChangeRequest
from app.schemas import PetCreate
from app.schemas import PetResponse
from app.schemas import PetUpdate
from app.schemas import RegisterRequest
from app.schemas import TokenResponse
from app.schemas import UserResponse
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


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
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


@router.post("/pets", response_model=PetResponse, status_code=status.HTTP_201_CREATED, tags=["Pets"])
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
    values.setdefault("recorded_at", datetime.now(UTC))
    record = model(pet_id=pet_id, **values)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def list_records(
    model: type[RecordModel],
    pet_id: str,
    user: User,
    db: AsyncSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
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
    return list(await db.scalars(query))


async def owned_record(
    pet_id: str, record_id: str, user: User, db: AsyncSession, model: type[RecordModel]
) -> RecordModel:
    await owned_pet(pet_id, user, db)
    record = await db.get(model, record_id)
    if record is None or record.pet_id != pet_id:
        raise NotFoundError(model.__name__, record_id)
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
    return record


# ── Feeding Records ──────────────────────────────────────────────────────────

@router.get("/pets/{pet_id}/feedings", response_model=list[FeedingRecordResponse], tags=["Feedings"])
async def list_feedings(
    pet_id: str,
    user: CurrentUser,
    db: DB,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
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


@router.get("/pets/{pet_id}/feedings/{record_id}", response_model=FeedingRecordResponse, tags=["Feedings"])
async def get_feeding(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> FeedingRecord:
    return await owned_record(pet_id, record_id, user, db, FeedingRecord)


@router.patch("/pets/{pet_id}/feedings/{record_id}", response_model=FeedingRecordResponse, tags=["Feedings"])
async def update_feeding(
    pet_id: str, record_id: str, payload: FeedingUpdate, user: CurrentUser, db: DB
) -> FeedingRecord:
    return await update_record(pet_id, record_id, payload, user, db, FeedingRecord)


@router.delete("/pets/{pet_id}/feedings/{record_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Feedings"])
async def delete_feeding(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> None:
    record = await owned_record(pet_id, record_id, user, db, FeedingRecord)
    await db.delete(record)
    await db.commit()


# ── Excretion Records ────────────────────────────────────────────────────────

@router.get("/pets/{pet_id}/excretions", response_model=list[ExcretionRecordResponse], tags=["Excretions"])
async def list_excretions(
    pet_id: str,
    user: CurrentUser,
    db: DB,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
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


@router.get("/pets/{pet_id}/excretions/{record_id}", response_model=ExcretionRecordResponse, tags=["Excretions"])
async def get_excretion(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> ExcretionRecord:
    return await owned_record(pet_id, record_id, user, db, ExcretionRecord)


@router.patch("/pets/{pet_id}/excretions/{record_id}", response_model=ExcretionRecordResponse, tags=["Excretions"])
async def update_excretion(
    pet_id: str, record_id: str, payload: ExcretionUpdate, user: CurrentUser, db: DB
) -> ExcretionRecord:
    return await update_record(pet_id, record_id, payload, user, db, ExcretionRecord)


@router.delete("/pets/{pet_id}/excretions/{record_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Excretions"])
async def delete_excretion(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> None:
    record = await owned_record(pet_id, record_id, user, db, ExcretionRecord)
    await db.delete(record)
    await db.commit()


# ── Behavior Records ─────────────────────────────────────────────────────────

@router.get("/pets/{pet_id}/behaviors", response_model=list[BehaviorRecordResponse], tags=["Behaviors"])
async def list_behaviors(
    pet_id: str,
    user: CurrentUser,
    db: DB,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
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


@router.get("/pets/{pet_id}/behaviors/{record_id}", response_model=BehaviorRecordResponse, tags=["Behaviors"])
async def get_behavior(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> BehaviorRecord:
    return await owned_record(pet_id, record_id, user, db, BehaviorRecord)


@router.patch("/pets/{pet_id}/behaviors/{record_id}", response_model=BehaviorRecordResponse, tags=["Behaviors"])
async def update_behavior(
    pet_id: str, record_id: str, payload: BehaviorUpdate, user: CurrentUser, db: DB
) -> BehaviorRecord:
    return await update_record(pet_id, record_id, payload, user, db, BehaviorRecord)


@router.delete("/pets/{pet_id}/behaviors/{record_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Behaviors"])
async def delete_behavior(pet_id: str, record_id: str, user: CurrentUser, db: DB) -> None:
    record = await owned_record(pet_id, record_id, user, db, BehaviorRecord)
    await db.delete(record)
    await db.commit()


@router.get("/dashboard", tags=["Dashboard"])
async def dashboard(user: CurrentUser, db: DB) -> dict[str, int]:
    pet_ids = select(Pet.id).where(Pet.user_id == user.id)

    async def count(model: type[RecordModel]) -> int:
        return int(
            await db.scalar(
                select(func.count()).select_from(model).where(model.pet_id.in_(pet_ids))
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
    }
