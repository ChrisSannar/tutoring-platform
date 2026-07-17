
from fastapi import Request, Response

from app.application_context import ApplicationContext

def context_from(request: Request) -> ApplicationContext:
    return request.app.state.context

def set_session_cookies(
    response: Response,
    context: ApplicationContext,
    raw_session: str,
    raw_csrf: str,
) -> None:
    response.set_cookie(
        key=context.session_cookie_name,
        value=raw_session,
        secure=context.secure_cookies,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=90 * 24 * 60 * 60,
    )
    response.set_cookie(
        key=context.csrf_cookie_name,
        value=raw_csrf,
        secure=context.secure_cookies,
        httponly=False,
        samesite="strict",
        path="/",
        max_age=90 * 24 * 60 * 60,
    )
