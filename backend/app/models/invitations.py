from datetime import datetime
import re
from typing import Literal

from pydantic import BaseModel, field_validator


class InvitationDraftRequest(BaseModel):
    email: str
    display_name: str
    shared_personal_message: str
    private_tutor_note: str


class ManualInvitationRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def normalize_valid_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("email must be valid")
        return normalized


class TutorInvitationResponse(InvitationDraftRequest):
    id: str
    status: Literal["draft"]


class ActivatedInvitationResponse(BaseModel):
    id: str
    status: Literal["active"]
    invitation_url: str
    expires_at: datetime


class InvitationLinkChangeResponse(BaseModel):
    id: str
    status: Literal["active", "created"]
    invitation_url: str
    expires_at: datetime


class CreatedInvitationResponse(ActivatedInvitationResponse):
    email: str
    status: Literal["created"]


class InvitationLinkResponse(BaseModel):
    invitation_url: str


class TutorInvitationRecordResponse(InvitationDraftRequest):
    id: str
    status: Literal[
        "draft", "active", "created", "opened", "claimed", "revoked", "expired"
    ]
    expires_at: datetime | None


class InviteeInvitationResponse(BaseModel):
    email: str
    display_name: str
    shared_personal_message: str


class InvitationEmailCorrectionRequest(BaseModel):
    email: str


class CorrectedInvitationResponse(BaseModel):
    id: str
    email: str
    status: Literal["draft", "active", "created", "opened"]


class RevokedInvitationResponse(BaseModel):
    id: str
    status: Literal["revoked"]
