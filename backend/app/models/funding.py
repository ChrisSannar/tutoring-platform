from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CreditAdjustmentRequest(BaseModel):
    quantity: int
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("quantity")
    @classmethod
    def require_nonzero_quantity(cls, value: int) -> int:
        if value == 0:
            raise ValueError("quantity must not be zero")
        return value

    @field_validator("reason")
    @classmethod
    def require_visible_reason(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("reason must contain text")
        return normalized


class CreditBalanceResponse(BaseModel):
    session_credits: int


class CreditLedgerEventResponse(BaseModel):
    id: str
    event_type: str
    quantity: int
    reason: str | None
    created_at: datetime


class CreditLedgerResponse(BaseModel):
    events: list[CreditLedgerEventResponse]
