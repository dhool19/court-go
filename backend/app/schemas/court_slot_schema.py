from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class SlotGenerate(BaseModel):
    date: date


class SlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    court_id: int
    starts_at: datetime
    ends_at: datetime
    is_blocked: bool
    is_booked: bool


class SlotUpdate(BaseModel):
    is_blocked: bool
