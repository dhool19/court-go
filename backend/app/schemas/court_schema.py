from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourtCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    sport_type: Literal["badminton", "tennis", "football"]
    hourly_price: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    description: str | None = Field(default=None, min_length=1, max_length=500)


class CourtUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    sport_type: Literal["badminton", "tennis", "football"] | None = None
    hourly_price: Decimal | None = Field(
        default=None, gt=0, max_digits=8, decimal_places=2
    )
    description: str | None = Field(default=None, min_length=1, max_length=500)

    @field_validator("name", "sport_type", "hourly_price")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")

        return value


class CourtResponse(CourtCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
