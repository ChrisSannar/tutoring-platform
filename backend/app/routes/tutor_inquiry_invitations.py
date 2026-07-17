from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.http.security import require_mutation
from app.invitations import create_invitation_from_inquiry
from app.models.invitations import CreatedInvitationResponse

router = APIRouter()


@router.post(
    "/api/tutor/inquiries/{inquiry_id}/invitation",
    status_code=201,
    response_model=CreatedInvitationResponse,
)
async def create_linked_invitation(
    inquiry_id: str, request: Request
) -> CreatedInvitationResponse:
    require_mutation(request, "tutor")
    settings = context_from(request).settings
    created = create_invitation_from_inquiry(
        settings.database_url,
        inquiry_id,
        settings.invitation_ttl_seconds,
        settings.invitation_encryption_key.get_secret_value(),
    )
    if created is None:
        raise HTTPException(status_code=404)
    return CreatedInvitationResponse.model_validate(created)
