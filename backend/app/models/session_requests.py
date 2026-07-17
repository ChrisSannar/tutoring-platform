from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator


class SessionRequestSubmission(BaseModel):
    service: str
    preferred_start: datetime
    timezone: str
    message: str | None = Field(default=None, max_length=1000)

    @field_validator("timezone")
    @classmethod
    def require_iana_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("timezone must be an IANA timezone") from error
        return value


class SessionRequestResponse(BaseModel):
    id: str
    service: str
    preferred_start: datetime
    timezone: str
    message: str | None
    status: Literal["pending"]


class SessionRequestStudentResponse(BaseModel):
    id: str
    email: str
    display_name: str


class TutorSessionRequestResponse(SessionRequestResponse):
    student: SessionRequestStudentResponse


class TutorSessionRequestListResponse(BaseModel):
    requests: list[TutorSessionRequestResponse]
