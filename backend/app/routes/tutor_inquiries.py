from fastapi import APIRouter, Request, Response
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.http.security import require_mutation, require_session
from app.inquiries import archive_inquiry, delete_inquiry, list_active_inquiries
from app.models.inquiries import InquiryDeletionConfirmation, TutorInquiryListResponse

router = APIRouter()


@router.get("/api/tutor/inquiries", response_model=TutorInquiryListResponse)
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
