from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.http.security import require_session
from app.invitations import retrieve_invitation_link
from app.models.invitations import InvitationLinkResponse

router = APIRouter()


@router.get(
    "/api/tutor/invitations/{invitation_id}/link",
    response_model=InvitationLinkResponse,
)
async def copy_invitation_link(
    invitation_id: str, request: Request
) -> InvitationLinkResponse:
    require_session(request, "tutor")
    settings = context_from(request).settings
    invitation_url = retrieve_invitation_link(
        settings.database_url,
        invitation_id,
        settings.invitation_encryption_key.get_secret_value(),
    )
    if invitation_url is None:
        raise HTTPException(status_code=404)
    return InvitationLinkResponse(invitation_url=invitation_url)
