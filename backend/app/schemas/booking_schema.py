from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class BookingCreate(BaseModel):
    slot_id: int = Field(gt=0)


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    slot_id: int
    booked_price: Decimal
    status: str
