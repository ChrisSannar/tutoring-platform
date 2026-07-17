from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.invitations import (
    activate_invitation,
    create_draft_invitation,
    create_manual_invitation,
    get_tutor_invitation,
)
from app.models.invitations import (
    ActivatedInvitationResponse,
    CreatedInvitationResponse,
    InvitationDraftRequest,
    ManualInvitationRequest,
    TutorInvitationRecordResponse,
    TutorInvitationResponse,
)
from app.http.security import require_mutation, require_session

router = APIRouter()


@router.post(
    "/api/tutor/invitations",
    status_code=201,
    response_model=TutorInvitationResponse | CreatedInvitationResponse,
)
async def create_invitation(
    invitation: InvitationDraftRequest | ManualInvitationRequest, request: Request
) -> TutorInvitationResponse | CreatedInvitationResponse:
    require_mutation(request, "tutor")
    settings = context_from(request).settings
    database_url = settings.database_url
    if isinstance(invitation, ManualInvitationRequest):
        created = create_manual_invitation(
            database_url,
            invitation.email,
            settings.invitation_ttl_seconds,
            settings.invitation_encryption_key.get_secret_value(),
        )
        return CreatedInvitationResponse.model_validate(created)
    created = create_draft_invitation(
        database_url,
        invitation.email,
        invitation.display_name,
        invitation.shared_personal_message,
        invitation.private_tutor_note,
    )
    return TutorInvitationResponse.model_validate(created)


@router.post(
    "/api/tutor/invitations/{invitation_id}/activate",
    response_model=ActivatedInvitationResponse,
)
async def activate_draft_invitation(
    invitation_id: str, request: Request
) -> ActivatedInvitationResponse:
    require_mutation(request, "tutor")
    settings = context_from(request).settings
    activated = activate_invitation(
        settings.database_url,
        invitation_id,
        settings.invitation_ttl_seconds,
        settings.invitation_encryption_key.get_secret_value(),
    )
    if activated is None:
        raise HTTPException(status_code=404)
    return ActivatedInvitationResponse.model_validate(activated)


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
