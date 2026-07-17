from fastapi import Request
from starlette.exceptions import HTTPException

from app.authentication import active_session, session_authorizes_mutation
from app.http.context import context_from


def require_session(request: Request, role: str) -> str:
    context = context_from(request)
    raw_session = request.cookies.get(context.session_cookie_name)
    if raw_session is None or active_session(
        context.settings.database_url,
        raw_session,
        context.settings.session_inactivity_seconds,
    ) != role:
        raise HTTPException(status_code=401)
    return raw_session


def require_mutation(request: Request, role: str) -> str:
    context = context_from(request)
    raw_session = request.cookies.get(context.session_cookie_name)
    raw_csrf = request.headers.get("x-csrf-token")
    if raw_session is None:
        raise HTTPException(status_code=401)
    if raw_csrf is None or not session_authorizes_mutation(
        context.settings.database_url, raw_session, raw_csrf, role
    ):
        raise HTTPException(status_code=403)
    if request.headers.get("origin") != context.settings.application_origin:
        raise HTTPException(status_code=403)
    return raw_session
