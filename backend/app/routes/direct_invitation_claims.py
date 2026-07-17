from fastapi import APIRouter, Request, Response
from starlette.exceptions import HTTPException

from app.funding import student_funding_summary
from app.http.context import context_from, set_session_cookies
from app.http.security import require_session
from app.invitations import InvitationClaimConflict, claim_direct_invitation
from app.models.invitation_claims import (
    ClaimedInvitationResponse,
    DirectInvitationClaimRequest,
    StudentFundingResponse,
)

router = APIRouter()


@router.post(
    "/api/invitations/{token}/claim", response_model=ClaimedInvitationResponse
)
async def claim_original_invitation(
    token: str, claim: DirectInvitationClaimRequest, request: Request, response: Response
) -> ClaimedInvitationResponse:
    context = context_from(request)
    try:
        claimed = claim_direct_invitation(
            context.settings.database_url,
            token,
            claim.display_name.strip(),
            context.settings.session_inactivity_seconds,
            context.settings.session_absolute_seconds,
            request.cookies.get(context.session_cookie_name),
        )
    except InvitationClaimConflict:
        raise HTTPException(status_code=409) from None
    if claimed is None:
        raise HTTPException(status_code=409)
    set_session_cookies(response, context, claimed["session"], claimed["csrf_token"])
    return ClaimedInvitationResponse.model_validate(claimed)


@router.get("/api/student/funding", response_model=StudentFundingResponse)
async def view_student_funding(request: Request) -> StudentFundingResponse:
    raw_session = require_session(request, "student")
    summary = student_funding_summary(
        context_from(request).settings.database_url, raw_session
    )
    return StudentFundingResponse.model_validate(summary)
