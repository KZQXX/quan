"""Daily stats aggregation service — computes per-pet daily summaries.

Called by the scheduler (midnight) and on-demand by the API.
"""

import logging
from datetime import UTC
from datetime import date
from datetime import datetime

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_stats import DailyStats
from app.models.pet import Pet
from app.models.record import BehaviorRecord
from app.models.record import ExcretionRecord
from app.models.record import FeedingRecord

logger = logging.getLogger(__name__)

RecordModel = FeedingRecord | ExcretionRecord | BehaviorRecord


async def aggregate_daily_stats(
    db: AsyncSession, target_date: date | None = None
) -> int:
    """Aggregate yesterday's stats for all pets.

    Returns the number of DailyStats rows created (one per pet).
    Uses upsert: if a row already exists for (pet_id, date), it updates it.
    """
    if target_date is None:
        target_date = date.today()
    date_str = target_date.isoformat()

    # Compute start/end bounds for that day in UTC
    start_dt = datetime(target_date.year, target_date.month, target_date.day, tzinfo=UTC)
    from datetime import timedelta

    end_dt = start_dt + timedelta(days=1)

    async def _count_records(model: type[RecordModel], pet_id: str) -> int:
        col = model.recorded_at
        result = await db.scalar(
            select(func.count())
            .select_from(model)
            .where(model.pet_id == pet_id, col >= start_dt, col < end_dt)
        )
        return int(result or 0)

    async def _sum_duration(pet_id: str) -> int:
        result = await db.scalar(
            select(func.coalesce(func.sum(BehaviorRecord.duration_minutes), 0))
            .select_from(BehaviorRecord)
            .where(
                BehaviorRecord.pet_id == pet_id,
                BehaviorRecord.recorded_at >= start_dt,
                BehaviorRecord.recorded_at < end_dt,
            )
        )
        return int(result or 0)

    # Fetch all user-pet pairs
    pet_rows = list((await db.execute(select(Pet.id, Pet.user_id))).all())
    if not pet_rows:
        return 0

    created = 0
    for pet_id, user_id in pet_rows:
        # Check if row exists
        existing = await db.scalar(
            select(DailyStats).where(
                DailyStats.pet_id == pet_id, DailyStats.date == date_str
            )
        )

        feeding_count = await _count_records(FeedingRecord, pet_id)
        excretion_count = await _count_records(ExcretionRecord, pet_id)
        behavior_count = await _count_records(BehaviorRecord, pet_id)
        total_duration = await _sum_duration(pet_id)

        if existing:
            existing.feeding_count = feeding_count
            existing.excretion_count = excretion_count
            existing.behavior_count = behavior_count
            existing.total_duration_minutes = total_duration
        else:
            row = DailyStats(
                user_id=user_id,
                pet_id=pet_id,
                date=date_str,
                feeding_count=feeding_count,
                excretion_count=excretion_count,
                behavior_count=behavior_count,
                total_duration_minutes=total_duration,
            )
            db.add(row)
        created += 1

    await db.commit()
    logger.info("Aggregated daily stats for %s: %d pets", date_str, created)
    return created


async def get_daily_stats(
    db: AsyncSession,
    user_id: str,
    pet_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[DailyStats]:
    """Query aggregated daily stats with optional filters."""
    conditions = [DailyStats.user_id == user_id]
    if pet_id:
        conditions.append(DailyStats.pet_id == pet_id)
    if start_date:
        conditions.append(DailyStats.date >= start_date)
    if end_date:
        conditions.append(DailyStats.date <= end_date)

    result = await db.scalars(
        select(DailyStats)
        .where(*conditions)
        .order_by(DailyStats.date.desc(), DailyStats.pet_id)
    )
    return list(result)
