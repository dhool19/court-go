from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta, time, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.dependencies import require_admin
from models.slot_model import CourtSlot
from models.court_model import Court
from models.reservation_model import SlotReservation
from db.database import get_db
from schemas.court_slot_schema import SlotGenerate, SlotResponse, SlotUpdate

router = APIRouter(prefix="/courts", tags=["Slots"])

CENTRE_TIMEZONE = ZoneInfo("Europe/Berlin")


@router.post(
    "/{court_id}/slots/generate",
    dependencies=[Depends(require_admin)],
)
async def generate_slots(
    court_id: int,
    data: SlotGenerate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Court).where(Court.id == court_id).with_for_update()
    )
    court = result.scalar_one_or_none()

    if court is None:
        raise HTTPException(status_code=404, detail="Court not found")

    if not court.is_active:
        raise HTTPException(status_code=409, detail="Court is inactive")

    now = datetime.now(timezone.utc)
    today = now.astimezone(CENTRE_TIMEZONE).date()

    if not today <= data.date <= today + timedelta(days=30):
        raise HTTPException(
            status_code=422,
            detail="Choose a date from today to 30 days ahead",
        )

    existing_result = await db.execute(
        select(CourtSlot.starts_at).where(CourtSlot.court_id == court_id)
    )

    existing_starts = set(existing_result.scalars().all())

    created_count = 0

    for hour in range(8, 22):
        local_start = datetime.combine(
            data.date,
            time(hour=hour),
            tzinfo=CENTRE_TIMEZONE,
        )
        utc_start = local_start.astimezone(timezone.utc)

        if utc_start <= now:
            continue

        starts_at = utc_start.replace(tzinfo=None)

        if starts_at in existing_starts:
            continue

        slot = CourtSlot(
            court_id=court_id,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
        )

        db.add(slot)
        created_count += 1

    await db.commit()

    return {"created_slots": created_count}


@router.get("/{court_id}/slots", response_model=list[SlotResponse])
async def lists_slot(
    court_id: int, selected_date: date, db: AsyncSession = Depends(get_db)
):
    court = await db.get(Court, court_id)
    if court is None:
        raise HTTPException(status_code=404, detail="Court not found")

    local_start = datetime.combine(
        selected_date,
        time.min,
        tzinfo=CENTRE_TIMEZONE,
    )

    local_end = datetime.combine(
        selected_date + timedelta(days=1),
        time.min,
        tzinfo=CENTRE_TIMEZONE,
    )

    utc_start = local_start.astimezone(timezone.utc).replace(tzinfo=None)
    utc_end = local_end.astimezone(timezone.utc).replace(tzinfo=None)

    query = (
        select(CourtSlot, SlotReservation.slot_id)
        .outerjoin(
            SlotReservation,
            SlotReservation.slot_id == CourtSlot.id,
        )
        .where(
            CourtSlot.court_id == court_id,
            CourtSlot.starts_at >= utc_start,
            CourtSlot.starts_at < utc_end,
        )
        .order_by(CourtSlot.starts_at)
    )

    result = await db.execute(query)

    return [
        SlotResponse(
            id=slot.id,
            court_id=slot.court_id,
            starts_at=slot.starts_at.replace(tzinfo=timezone.utc),
            ends_at=slot.ends_at.replace(tzinfo=timezone.utc),
            is_blocked=slot.is_blocked,
            is_booked=reserved_slot_id is not None,
        )
        for slot, reserved_slot_id in result.all()
    ]


@router.patch(
    "/{court_id}/slots/{slot_id}",
    dependencies=[Depends(require_admin)],
)
async def update_slot(
    court_id: int,
    slot_id: int,
    data: SlotUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CourtSlot)
        .where(
            CourtSlot.id == slot_id,
            CourtSlot.court_id == court_id,
        )
        .with_for_update()
    )

    slot = result.scalar_one_or_none()
    if slot is None:
        raise HTTPException(status_code=404, detail="Slot not found")

    if data.is_blocked:
        reservation_result = await db.execute(
            select(SlotReservation)
            .where(SlotReservation.slot_id == slot.id)
            .with_for_update()
        )
        reservation = reservation_result.scalar_one_or_none()

        if reservation is not None:
            raise HTTPException(
                status_code=409,
                detail="Cancel the booking before blocking this slot",
            )

    slot.is_blocked = data.is_blocked
    await db.commit()

    return {
        "slot_id": slot.id,
        "is_blocked": slot.is_blocked,
    }
