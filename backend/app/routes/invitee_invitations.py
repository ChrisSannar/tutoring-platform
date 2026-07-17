from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.invitations import get_active_invitation_by_token, issue_invitation_claim_token
from app.models.auth import MagicLinkAcceptedResponse
from app.models.invitation_claims import InvitationClaimLinkRequest
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


@router.post(
    "/api/invitations/{token}/magic-links",
    status_code=202,
    response_model=MagicLinkAcceptedResponse,
)
async def request_invitation_claim_link(
    token: str, submission: InvitationClaimLinkRequest, request: Request
) -> MagicLinkAcceptedResponse:
    context = context_from(request)
    email = submission.email.strip().lower()
    claim_token = issue_invitation_claim_token(
        context.settings.database_url,
        token,
        email,
        context.settings.magic_link_ttl_seconds,
    )
    if claim_token is not None and context.settings.environment != "production":
        context.development_outbox.append(
            {"to": email, "magic_link": f"/student/claim/confirm?token={claim_token}"}
        )
    return MagicLinkAcceptedResponse(
        status="accepted",
        message="If the address matches, a verification link has been sent.",
    )
