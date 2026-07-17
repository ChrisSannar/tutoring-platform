from typing import Literal

from pydantic import BaseModel


class InvitationClaimLinkRequest(BaseModel):
    email: str


class InvitationClaimConfirmationResponse(BaseModel):
    status: Literal["confirmation_required"]
    email: str
    display_name: str


class InvitationClaimConfirmationRequest(BaseModel):
    token: str
    display_name: str


class ClaimedInvitationResponse(BaseModel):
    status: Literal["claimed"]
    role: Literal["student"]
    email: str
    display_name: str
    csrf_token: str
