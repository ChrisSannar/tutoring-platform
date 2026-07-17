from datetime import datetime, time

from pydantic import BaseModel, Field, model_validator


class AvailabilityWindowInput(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def valid_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must precede end_time")
        return self


class AvailabilityWindowResponse(AvailabilityWindowInput):
    id: str


class BlockedTimeInput(BaseModel):
    start_at: datetime
    end_at: datetime
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def valid_range(self):
        if self.start_at >= self.end_at:
            raise ValueError("start_at must precede end_at")
        return self


class BlockedTimeResponse(BlockedTimeInput):
    id: str


class BookableSlot(BaseModel):
    start_at: datetime
    end_at: datetime


class BookableSlotList(BaseModel):
    tutor_timezone: str
    slots: list[BookableSlot]
