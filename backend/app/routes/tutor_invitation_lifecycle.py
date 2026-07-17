from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.invitations import (
    correct_invitation_email,
    regenerate_invitation,
    revoke_invitation,
)
from app.models.invitations import (
    ActivatedInvitationResponse,
    CorrectedInvitationResponse,
    InvitationEmailCorrectionRequest,
    RevokedInvitationResponse,
)
from app.http.security import require_mutation

router = APIRouter()


@router.patch(
    "/api/tutor/invitations/{invitation_id}",
    response_model=CorrectedInvitationResponse,
)
async def correct_bound_email(
    invitation_id: str,
    correction: InvitationEmailCorrectionRequest,
    request: Request,
) -> CorrectedInvitationResponse:
    require_mutation(request, "tutor")
    corrected = correct_invitation_email(
        context_from(request).settings.database_url, invitation_id, correction.email
    )
    if corrected is None:
        raise HTTPException(status_code=404)
    return CorrectedInvitationResponse.model_validate(corrected)


@router.post(
    "/api/tutor/invitations/{invitation_id}/revoke",
    response_model=RevokedInvitationResponse,
)
async def revoke_active_invitation(
    invitation_id: str, request: Request
) -> RevokedInvitationResponse:
    require_mutation(request, "tutor")
    revoked = revoke_invitation(
        context_from(request).settings.database_url, invitation_id
    )
    if revoked is None:
        raise HTTPException(status_code=404)
    return RevokedInvitationResponse.model_validate(revoked)


@router.post(
    "/api/tutor/invitations/{invitation_id}/regenerate",
    response_model=ActivatedInvitationResponse,
)
async def regenerate_active_invitation(
    invitation_id: str, request: Request
) -> ActivatedInvitationResponse:
    require_mutation(request, "tutor")
    settings = context_from(request).settings
    regenerated = regenerate_invitation(
        settings.database_url, invitation_id, settings.invitation_ttl_seconds
    )
    if regenerated is None:
        raise HTTPException(status_code=404)
    return ActivatedInvitationResponse.model_validate(regenerated)
