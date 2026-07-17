from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class InvitationDraftRequest(BaseModel):
    email: str
    display_name: str
    shared_personal_message: str
    private_tutor_note: str


class TutorInvitationResponse(InvitationDraftRequest):
    id: str
    status: Literal["draft"]


class ActivatedInvitationResponse(BaseModel):
    id: str
    status: Literal["active"]
    invitation_url: str
    expires_at: datetime


class TutorInvitationRecordResponse(InvitationDraftRequest):
    id: str
    status: Literal["draft", "active", "claimed", "revoked", "expired"]
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
    status: Literal["draft", "active"]


class RevokedInvitationResponse(BaseModel):
    id: str
    status: Literal["revoked"]
