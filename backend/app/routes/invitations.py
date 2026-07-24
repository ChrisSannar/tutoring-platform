from fastapi import APIRouter, Request, Response
from starlette.exceptions import HTTPException

from app.funding import student_funding_summary
from app.http import context_from, require_mutation, require_session, set_session_cookies
from app.inquiries import archive_inquiry, create_inquiry, delete_inquiry, list_active_inquiries
from app.invitations import (
    InvitationClaimConflict,
    claim_direct_invitation,
    correct_invitation_email,
    create_invitation_from_inquiry,
    create_manual_invitation,
    get_active_invitation_by_token,
    get_tutor_invitation,
    regenerate_invitation,
    retrieve_invitation_link,
    revoke_invitation,
)
from app.models import (
    ClaimedInvitationResponse,
    CorrectedInvitationResponse,
    CreatedInvitationResponse,
    DirectInvitationClaimRequest,
    InquiryAcceptedResponse,
    InquiryDeletionConfirmation,
    InquirySubmission,
    InvitationEmailCorrectionRequest,
    InvitationLinkChangeResponse,
    InvitationLinkResponse,
    InviteeInvitationResponse,
    ManualInvitationRequest,
    RevokedInvitationResponse,
    StudentFundingResponse,
    TutorInquiryListResponse,
    TutorInvitationRecordResponse,
)

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


@router.post(
    "/api/inquiries", status_code=202, response_model=InquiryAcceptedResponse
)
async def submit_inquiry(
    submission: InquirySubmission, request: Request
) -> InquiryAcceptedResponse:
    settings = context_from(request).settings
    accepted = create_inquiry(
        settings.database_url,
        submission.email,
        submission.message,
        request.client.host if request.client else "unknown",
        settings.inquiry_ip_hourly_limit,
    )
    if not accepted:
        raise HTTPException(status_code=429)
    return InquiryAcceptedResponse(
        message="Thanks. Your tutoring request has been received."
    )


@router.get(
    "/api/tutor/inquiries",
    response_model=TutorInquiryListResponse,
    response_model_exclude_none=True,
)
async def view_active_inquiries(request: Request) -> TutorInquiryListResponse:
    require_session(request, "tutor")
    inquiries = list_active_inquiries(context_from(request).settings.database_url)
    return TutorInquiryListResponse.model_validate({"inquiries": inquiries})


@router.post("/api/tutor/inquiries/{inquiry_id}/archive", status_code=204)
async def archive_active_inquiry(inquiry_id: str, request: Request) -> Response:
    require_mutation(request, "tutor")
    if not archive_inquiry(
        context_from(request).settings.database_url, inquiry_id
    ):
        raise HTTPException(status_code=404)
    return Response(status_code=204)


@router.delete("/api/tutor/inquiries/{inquiry_id}", status_code=204)
async def permanently_delete_inquiry(
    inquiry_id: str, confirmation: InquiryDeletionConfirmation, request: Request
) -> Response:
    require_mutation(request, "tutor")
    if not delete_inquiry(context_from(request).settings.database_url, inquiry_id):
        raise HTTPException(status_code=404)
    return Response(status_code=204)


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
    if corrected["status"] == "conflict":
        raise HTTPException(status_code=409)
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
    if revoked["status"] == "conflict":
        raise HTTPException(status_code=409)
    return RevokedInvitationResponse.model_validate(revoked)


@router.post(
    "/api/tutor/invitations/{invitation_id}/regenerate",
    response_model=InvitationLinkChangeResponse,
)
async def regenerate_active_invitation(
    invitation_id: str, request: Request
) -> InvitationLinkChangeResponse:
    require_mutation(request, "tutor")
    settings = context_from(request).settings
    regenerated = regenerate_invitation(
        settings.database_url,
        invitation_id,
        settings.invitation_ttl_seconds,
        settings.invitation_encryption_key.get_secret_value(),
    )
    if regenerated is None:
        raise HTTPException(status_code=404)
    if regenerated["status"] == "conflict":
        raise HTTPException(status_code=409)
    return InvitationLinkChangeResponse.model_validate(regenerated)


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
