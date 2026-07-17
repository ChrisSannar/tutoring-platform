from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator


class TutorSettingsUpdate(BaseModel):
    currency: Literal["USD"]
    session_price_cents: int = Field(gt=0, le=1_000_000)
    tutor_timezone: str
    default_meeting_details: str | None = Field(default=None, max_length=5000)

    @field_validator("tutor_timezone")
    @classmethod
    def require_iana_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("tutor_timezone must be an IANA timezone") from error
        return value


class TutorSettingsResponse(TutorSettingsUpdate):
    pass
