from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CheckoutInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_at: datetime
    focus: str | None = Field(default=None, max_length=500)


class CheckoutResponse(BaseModel):
    checkout_session_id: str
    checkout_url: str
    amount_cents: int
    currency: Literal["USD"]
    status: Literal["pending", "fulfilled", "expired", "mismatch"]
