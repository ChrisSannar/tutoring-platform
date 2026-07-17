from typing import Literal

from pydantic import BaseModel, Field, field_validator


class InvitationClaimLinkRequest(BaseModel):
    email: str


class InvitationClaimConfirmationResponse(BaseModel):
    status: Literal["confirmation_required"]
    email: str
    display_name: str


class InvitationClaimConfirmationRequest(BaseModel):
    token: str
    display_name: str


class DirectInvitationClaimRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)

    @field_validator("display_name")
    @classmethod
    def require_visible_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("display name must contain text")
        return normalized


class StudentFundingResponse(BaseModel):
    first_session_promotion: Literal["available", "unavailable"]
    session_credits: int


class ClaimedInvitationResponse(BaseModel):
    status: Literal["claimed"]
    role: Literal["student"]
    email: str
    display_name: str
    csrf_token: str
