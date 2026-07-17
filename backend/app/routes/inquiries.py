from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.inquiries import create_inquiry
from app.models.inquiries import InquiryAcceptedResponse, InquirySubmission

router = APIRouter()


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
