from fastapi import APIRouter, Request, Response
from starlette.exceptions import HTTPException

from app.http.context import context_from, set_session_cookies
from app.invitations import (
    InvitationClaimConflict,
    claim_invitation,
    get_active_invitation_claim,
)
from app.models.invitation_claims import (
    ClaimedInvitationResponse,
    InvitationClaimConfirmationRequest,
    InvitationClaimConfirmationResponse,
)

router = APIRouter()


@router.get(
    "/api/invitation-claims/confirm",
    response_model=InvitationClaimConfirmationResponse,
)
async def inspect_invitation_claim(
    token: str, request: Request
) -> InvitationClaimConfirmationResponse:
    invitation = get_active_invitation_claim(
        context_from(request).settings.database_url, token
    )
    if invitation is None:
        raise HTTPException(status_code=400)
    return InvitationClaimConfirmationResponse(
        status="confirmation_required",
        email=invitation["email"],
        display_name=invitation["display_name"],
    )


@router.post(
    "/api/invitation-claims/confirm", response_model=ClaimedInvitationResponse
)
async def confirm_invitation_claim(
    confirmation: InvitationClaimConfirmationRequest,
    request: Request,
    response: Response,
) -> ClaimedInvitationResponse:
    context = context_from(request)
    settings = context.settings
    try:
        claimed = claim_invitation(
            settings.database_url,
            confirmation.token,
            confirmation.display_name,
            settings.session_inactivity_seconds,
            settings.session_absolute_seconds,
            request.cookies.get(context.session_cookie_name),
        )
    except InvitationClaimConflict:
        raise HTTPException(status_code=409) from None
    if claimed is None:
        raise HTTPException(status_code=400)
    set_session_cookies(
        response, context, claimed["session"], claimed["csrf_token"]
    )
    return ClaimedInvitationResponse.model_validate(claimed)
