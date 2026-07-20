from datetime import datetime
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class ManualInvitationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str

    @field_validator("email")
    @classmethod
    def normalize_valid_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("email must be valid")
        return normalized


class CreatedInvitationResponse(BaseModel):
    id: str
    email: str
    status: Literal["created"]
    invitation_url: str
    expires_at: datetime


class InvitationLinkChangeResponse(BaseModel):
    id: str
    status: Literal["created"]
    invitation_url: str
    expires_at: datetime


class InvitationLinkResponse(BaseModel):
    invitation_url: str


class TutorInvitationRecordResponse(BaseModel):
    id: str
    email: str
    display_name: str
    shared_personal_message: str
    private_tutor_note: str
    status: Literal["created", "opened", "claimed", "revoked", "expired"]
    created_at: datetime
    first_opened_at: datetime | None
    claimed_at: datetime | None
    expired_at: datetime | None
    revoked_at: datetime | None
    expires_at: datetime | None


class InviteeInvitationResponse(BaseModel):
    email: str


class InvitationEmailCorrectionRequest(BaseModel):
    email: str


class CorrectedInvitationResponse(BaseModel):
    id: str
    email: str
    status: Literal["created", "opened"]


class RevokedInvitationResponse(BaseModel):
    id: str
    status: Literal["revoked"]
