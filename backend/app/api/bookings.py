from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from models.user_model import User
from models.court_model import Court
from models.slot_model import CourtSlot
from models.reservation_model import SlotReservation
from models.booking_model import Booking
from api.dependencies import get_current_user
from db.database import get_db
from schemas.booking_schema import BookingCreate, BookingResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Booking)

    if current_user.role != "admin":
        query = query.where(Booking.customer_id == current_user.id)

    query = query.order_by(Booking.id.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(
    data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CourtSlot).where(CourtSlot.id == data.slot_id).with_for_update()
    )
    slot = result.scalar_one_or_none()

    if slot is None:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot.is_blocked:
        raise HTTPException(status_code=409, detail="Slot is blocked for maintenance")

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if slot.starts_at <= now:
        raise HTTPException(status_code=409, detail="Slot has already started")

    if slot.starts_at > now + timedelta(days=30):
        raise HTTPException(
            status_code=422, detail="Slot is outside the booking window"
        )

    court_result = await db.execute(
        select(Court).where(Court.id == slot.court_id).with_for_update()
    )
    court = court_result.scalar_one()

    if not court.is_active:
        raise HTTPException(status_code=409, detail="Court is inactive")

    booking = Booking(
        customer_id=current_user.id,
        slot_id=slot.id,
        booked_price=court.hourly_price,
        status="confirmed",
    )

    try:
        db.add(booking)
        await db.flush()

        reservation = SlotReservation(
            slot_id=slot.id,
            booking_id=booking.id,
            customer_id=current_user.id,
            starts_at=slot.starts_at,
        )
        db.add(reservation)
        await db.commit()
        await db.refresh(booking)

    except IntegrityError as e:
        await db.rollback()

        print("database error", e.orig)

        if e.orig.args[0] == 1062:
            raise HTTPException(status_code=409, detail="This slot is already booked")

        raise HTTPException(
            status_code=400,
            detail="Could not complete booking due to a database conflict",
        )

    return booking


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Booking).where(Booking.id == booking_id)

    if current_user.role != "admin":
        query = query.where(Booking.customer_id == current_user.id)

    result = await db.execute(query.with_for_update())
    booking = result.scalar_one_or_none()

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == "cancelled":
        return booking

    slot = await db.get(CourtSlot, booking.slot_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if slot.starts_at <= now:
        raise HTTPException(
            status_code=409, detail="Cannot cancel a booking that has already started"
        )

    reservation_result = await db.execute(
        select(SlotReservation)
        .where(SlotReservation.booking_id == booking_id)
        .with_for_update()
    )
    reservation = reservation_result.scalar_one_or_none()

    try:
        booking.status = "cancelled"

        if reservation is not None:
            await db.delete(reservation)

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    await db.refresh(booking)
    return booking
