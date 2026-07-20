from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.invitations import (
    create_manual_invitation,
    get_tutor_invitation,
)
from app.models.invitations import (
    CreatedInvitationResponse,
    ManualInvitationRequest,
    TutorInvitationRecordResponse,
)
from app.http.security import require_mutation, require_session

router = APIRouter()


@router.post(
    "/api/tutor/invitations",
    status_code=201,
    response_model=CreatedInvitationResponse,
)
async def create_invitation(
    invitation: ManualInvitationRequest, request: Request
) -> CreatedInvitationResponse:
    require_mutation(request, "tutor")
    settings = context_from(request).settings
    created = create_manual_invitation(
        settings.database_url,
        invitation.email,
        settings.invitation_ttl_seconds,
        settings.invitation_encryption_key.get_secret_value(),
    )
    return CreatedInvitationResponse.model_validate(created)


@router.get(
    "/api/tutor/invitations/{invitation_id}",
    response_model=TutorInvitationRecordResponse,
)
async def inspect_tutor_invitation(
    invitation_id: str, request: Request
) -> TutorInvitationRecordResponse:
    require_session(request, "tutor")
    invitation = get_tutor_invitation(
        context_from(request).settings.database_url, invitation_id
    )
    if invitation is None:
        raise HTTPException(status_code=404)
    return TutorInvitationRecordResponse.model_validate(invitation)
