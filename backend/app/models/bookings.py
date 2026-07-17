from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class StudentBookingInput(BaseModel):
    start_at: datetime
    focus: str | None = Field(default=None, max_length=500)
    confirmed: Literal[True]


class ComplimentaryBookingInput(BaseModel):
    start_at: datetime
    focus: str | None = Field(default=None, max_length=500)
    complimentary: Literal[True]
    override_id: str | None = None
    warning_acknowledged: bool = False


class BookingResponse(BaseModel):
    id: str
    start_at: datetime
    end_at: datetime
    duration_minutes: Literal[60]
    tutor_timezone: str
    funding_kind: Literal["first_session_promotion", "session_credit", "complimentary"]
    focus: str | None
    meeting_details: str | None
    price_cents: int
    currency: Literal["USD"]
    status: Literal["upcoming", "completed", "cancelled"]
