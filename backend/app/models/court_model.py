from decimal import Decimal
from sqlalchemy import Numeric, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Court(Base):
    __tablename__ = "courts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sport_type: Mapped[str] = mapped_column(String(100), nullable=False)
    hourly_price: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
