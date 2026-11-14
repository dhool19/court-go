from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class SlotReservation(Base):
    __tablename__ = "slot_reservation"

    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "starts_at",
            name="uq_customer_reservation_start",
        ),
    )

    slot_id: Mapped[int] = mapped_column(ForeignKey("booking.id"), primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("booking.id"), unique=True, nullable=False
    )
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
