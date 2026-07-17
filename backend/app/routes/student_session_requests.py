from fastapi import APIRouter, Header, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.models.session_requests import SessionRequestResponse, SessionRequestSubmission
from app.http.security import require_mutation, require_session
from app.session_requests import create_session_request, get_session_request

router = APIRouter()


@router.post(
    "/api/student/session-requests",
    status_code=201,
    response_model=SessionRequestResponse,
)
async def submit_session_request(
    submission: SessionRequestSubmission,
    request: Request,
    idempotency_key: str = Header(),
) -> SessionRequestResponse:
    raw_session = require_session(request, "student")
    require_mutation(request, "student")
    created = create_session_request(
        context_from(request).settings.database_url,
        raw_session,
        idempotency_key,
        submission.service,
        submission.preferred_start,
        submission.timezone,
        submission.message,
    )
    return SessionRequestResponse.model_validate(created)


@router.get(
    "/api/student/session-requests/{session_request_id}",
    response_model=SessionRequestResponse,
)
async def view_student_session_request(
    session_request_id: str, request: Request
) -> SessionRequestResponse:
    raw_session = require_session(request, "student")
    session_request = get_session_request(
        context_from(request).settings.database_url,
        raw_session,
        session_request_id,
    )
    if session_request is None:
        raise HTTPException(status_code=404)
    return SessionRequestResponse.model_validate(session_request)
