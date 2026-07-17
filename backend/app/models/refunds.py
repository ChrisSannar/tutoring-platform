from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class RefundRequestResponse(BaseModel):
    id: str
    booking_id: str
    amount_cents: int
    currency: Literal["USD"]
    status: Literal["pending", "declined", "refunded"]
    created_at: datetime


class RefundStudent(BaseModel):
    id: str
    display_name: str


class TutorRefundRequestResponse(RefundRequestResponse):
    student: RefundStudent


class StudentRefundList(BaseModel):
    refund_requests: list[RefundRequestResponse]


class TutorRefundList(BaseModel):
    refund_requests: list[TutorRefundRequestResponse]
