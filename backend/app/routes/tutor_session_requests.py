from fastapi import APIRouter, Request

from app.http.context import context_from
from app.models.session_requests import TutorSessionRequestListResponse
from app.http.security import require_session
from app.session_requests import list_business_session_requests

router = APIRouter()


@router.get(
    "/api/tutor/session-requests",
    response_model=TutorSessionRequestListResponse,
)
async def view_business_session_requests(
    request: Request,
) -> TutorSessionRequestListResponse:
    require_session(request, "tutor")
    requests = list_business_session_requests(
        context_from(request).settings.database_url
    )
    return TutorSessionRequestListResponse.model_validate({"requests": requests})
