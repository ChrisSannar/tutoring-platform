from fastapi import APIRouter, Request, Response
from starlette.exceptions import HTTPException

from app.authentication import active_session, revoke_session, student_session_details
from app.http.context import context_from
from app.http.security import require_session

router = APIRouter()


@router.get("/api/auth/session")
async def get_role_session(request: Request) -> dict[str, str]:
    context = context_from(request)
    raw_session = request.cookies.get(context.session_cookie_name)
    role = None if raw_session is None else active_session(
        context.settings.database_url,
        raw_session,
        context.settings.session_inactivity_seconds,
    )
    if role is None:
        raise HTTPException(status_code=401)
    return {"role": role}


@router.get("/api/tutor/session")
async def get_tutor_session(request: Request) -> dict[str, str]:
    require_session(request, "tutor")
    return {"role": "tutor"}


@router.get("/api/student/session")
async def get_student_session(request: Request) -> dict[str, str]:
    context = context_from(request)
    raw_session = require_session(request, "student")
    student = student_session_details(context.settings.database_url, raw_session)
    if student is None:
        raise HTTPException(status_code=401)
    return student


@router.post("/api/auth/logout", status_code=204)
async def logout(request: Request, response: Response) -> Response:
    context = context_from(request)
    if request.headers.get("origin") != context.settings.application_origin:
        raise HTTPException(status_code=403)
    raw_session = request.cookies.get(context.session_cookie_name)
    raw_csrf = request.headers.get("x-csrf-token")
    if (
        raw_session is None
        or raw_csrf is None
        or not revoke_session(context.settings.database_url, raw_session, raw_csrf)
    ):
        raise HTTPException(status_code=403)
    response.delete_cookie(context.session_cookie_name, path="/")
    response.delete_cookie(context.csrf_cookie_name, path="/")
    response.status_code = 204
    return response
