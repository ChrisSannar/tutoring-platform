from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.database import readiness_status
from app.authentication import (
    accept_magic_link_request,
    active_session,
    consume_magic_link,
    issue_magic_link,
    magic_link_is_active,
    revoke_session,
)


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadyResponse(BaseModel):
    status: Literal["ready"]


class MagicLinkRequest(BaseModel):
    email: str


class MagicLinkAcceptedResponse(BaseModel):
    status: Literal["accepted"]
    message: str


class MagicLinkConfirmation(BaseModel):
    token: str


def create_app() -> FastAPI:
    settings = get_settings()
    development_outbox: list[dict[str, str]] = []
    session_cookie_name = (
        "__Host-tutoring_session"
        if settings.environment == "production"
        else "tutoring_session"
    )
    csrf_cookie_name = (
        "__Host-tutoring_csrf"
        if settings.environment == "production"
        else "tutoring_csrf"
    )
    application = FastAPI(
        title="Tutoring Platform",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

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
            code = "not_found"
            message = "Resource not found"
        else:
            code = "request_failed"
            message = "Request failed"

        return JSONResponse(
            status_code=exception.status_code,
            content={
                "code": code,
                "message": message,
                "request_id": request.state.request_id,
            },
        )

    @application.get("/api/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.get("/api/ready", response_model=ReadyResponse)
    async def ready() -> ReadyResponse | JSONResponse:
        status = readiness_status(settings.database_url)
        if status == "ready":
            return ReadyResponse(status="ready")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": status},
        )

    @application.post(
        "/api/auth/magic-links",
        status_code=202,
        response_model=MagicLinkAcceptedResponse,
    )
    async def request_magic_link(
        magic_link_request: MagicLinkRequest, request: Request
    ) -> MagicLinkAcceptedResponse:
        normalized_email = magic_link_request.email.strip().lower()
        ip_address = request.client.host if request.client is not None else "unknown"
        if not accept_magic_link_request(
            settings.database_url, normalized_email, ip_address
        ):
            raise HTTPException(status_code=429)
        token = issue_magic_link(
            settings.database_url,
            normalized_email,
            settings.magic_link_ttl_seconds,
        )
        if token is not None and settings.environment != "production":
            development_outbox.append(
                {
                    "to": normalized_email,
                    "magic_link": f"/tutor/sign-in/confirm?token={token}",
                }
            )
        return MagicLinkAcceptedResponse(
            status="accepted",
            message="If the address is eligible, a sign-in link has been sent.",
        )

    if settings.environment != "production":

        @application.get("/api/development/outbox")
        async def get_development_outbox() -> dict[str, list[dict[str, str]]]:
            return {"messages": development_outbox}

    @application.get("/api/auth/magic-links/confirm")
    async def inspect_magic_link(token: str) -> dict[str, str]:
        if not magic_link_is_active(settings.database_url, token):
            raise HTTPException(status_code=400)
        return {"status": "confirmation_required"}

    @application.post("/api/auth/magic-links/confirm")
    async def confirm_magic_link(
        confirmation: MagicLinkConfirmation, request: Request, response: Response
    ) -> dict[str, str]:
        authenticated = consume_magic_link(
            settings.database_url,
            confirmation.token,
            settings.session_inactivity_seconds,
            settings.session_absolute_seconds,
            request.cookies.get(session_cookie_name),
        )
        if authenticated is None:
            raise HTTPException(status_code=400)
        raw_session, raw_csrf, role = authenticated
        response.set_cookie(
            key=session_cookie_name,
            value=raw_session,
            secure=settings.environment == "production",
            httponly=True,
            samesite="lax",
            path="/",
            max_age=90 * 24 * 60 * 60,
        )
        response.set_cookie(
            key=csrf_cookie_name,
            value=raw_csrf,
            secure=settings.environment == "production",
            httponly=False,
            samesite="strict",
            path="/",
            max_age=90 * 24 * 60 * 60,
        )
        return {"status": "authenticated", "role": role, "csrf_token": raw_csrf}

    @application.get("/api/tutor/session")
    async def get_tutor_session(request: Request) -> dict[str, str]:
        raw_session = request.cookies.get(session_cookie_name)
        if (
            raw_session is None
            or active_session(
                settings.database_url,
                raw_session,
                settings.session_inactivity_seconds,
            )
            != "tutor"
        ):
            raise HTTPException(status_code=401)
        return {"role": "tutor"}

    @application.post("/api/auth/logout", status_code=204)
    async def logout(request: Request, response: Response) -> Response:
        if request.headers.get("origin") != settings.application_origin:
            raise HTTPException(status_code=403)
        raw_session = request.cookies.get(session_cookie_name)
        raw_csrf = request.headers.get("x-csrf-token")
        if (
            raw_session is None
            or raw_csrf is None
            or not revoke_session(settings.database_url, raw_session, raw_csrf)
        ):
            raise HTTPException(status_code=403)
        response.delete_cookie(session_cookie_name, path="/")
        response.delete_cookie(csrf_cookie_name, path="/")
        response.status_code = 204
        return response

    return application


app = create_app()
