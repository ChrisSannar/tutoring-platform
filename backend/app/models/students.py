from typing import Literal

from pydantic import BaseModel


class TutorStudentResponse(BaseModel):
    id: str
    email: str
    display_name: str


class TutorStudentListResponse(BaseModel):
    students: list[TutorStudentResponse]


class StudentFundingSummary(BaseModel):
    first_session_promotion: Literal["available", "unavailable"]
    session_credits: int


class TutorStudentDetailResponse(TutorStudentResponse):
    funding: StudentFundingSummary
    pending_refund_requests: list[dict[str, str]]
    upcoming_booking: dict[str, str] | None
