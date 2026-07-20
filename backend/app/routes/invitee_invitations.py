from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.invitations import get_active_invitation_by_token
from app.models.invitations import InviteeInvitationResponse

router = APIRouter()


@router.get("/api/invitations/{token}", response_model=InviteeInvitationResponse)
@router.get("/invite/{token}", response_model=InviteeInvitationResponse)
async def open_invitation(token: str, request: Request) -> InviteeInvitationResponse:
    invitation = get_active_invitation_by_token(
        context_from(request).settings.database_url, token
    )
    if invitation is None:
        raise HTTPException(status_code=404)
    return InviteeInvitationResponse.model_validate(invitation)
