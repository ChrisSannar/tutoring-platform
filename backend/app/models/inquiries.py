import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class InquirySubmission(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("email")
    @classmethod
    def normalize_valid_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("email must be valid")
        return normalized

    @field_validator("message")
    @classmethod
    def require_context(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message must contain text")
        return normalized


class InquiryAcceptedResponse(BaseModel):
    message: str


class TutorInquiryResponse(BaseModel):
    id: str
    email: str
    message: str
    status: Literal["new", "invited"]


class TutorInquiryListResponse(BaseModel):
    inquiries: list[TutorInquiryResponse]


class InquiryDeletionConfirmation(BaseModel):
    confirmed: Literal[True]
