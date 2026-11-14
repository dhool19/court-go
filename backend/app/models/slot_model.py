from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class CourtSlot(Base):
    __tablename__ = "court_slots"

    __table_args__ = (
        UniqueConstraint(
            "court_id",
            "starts_at",
            name="uq_court_slot_start",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
