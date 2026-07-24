from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.application_context import ApplicationContext
from app.authentication import active_session, session_authorizes_mutation


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


def install_error_handling(application: FastAPI) -> None:
    @application.middleware("http")
    async def attach_request_id(request: Request, call_next) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @application.exception_handler(HTTPException)
    async def sanitized_http_error(
        request: Request, exception: HTTPException
    ) -> JSONResponse:
        if exception.status_code == 404:
            code, message = "not_found", "Resource not found"
        else:
            code, message = "request_failed", "Request failed"
        return JSONResponse(
            status_code=exception.status_code,
            content={
                "code": code,
                "message": message,
                "request_id": request.state.request_id,
            },
        )

    @application.exception_handler(RequestValidationError)
    async def sanitized_validation_error(
        request: Request, _exception: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "request_failed",
                "message": "Request failed",
                "request_id": request.state.request_id,
            },
        )


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
