from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Booking(Base):
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(primary_key=True)

    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    slot_id: Mapped[int] = mapped_column(
        ForeignKey("court_slots.id"), nullable=True, index=True
    )
    booked_price: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    status: Mapped[int] = mapped_column(String(20), default="confirmed", nullable=False)
