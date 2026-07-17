from fastapi import APIRouter, Request, Response
from starlette.exceptions import HTTPException

from app.authentication import (
    accept_magic_link_request,
    consume_magic_link,
    issue_magic_link,
    magic_link_is_active,
)
from app.http.context import context_from, set_session_cookies
from app.models.auth import (
    MagicLinkAcceptedResponse,
    MagicLinkConfirmation,
    MagicLinkRequest,
)

router = APIRouter()


@router.post(
    "/api/auth/magic-links", status_code=202, response_model=MagicLinkAcceptedResponse
)
async def request_magic_link(
    submission: MagicLinkRequest, request: Request
) -> MagicLinkAcceptedResponse:
    context = context_from(request)
    settings = context.settings
    email = submission.email.strip().lower()
    ip_address = request.client.host if request.client is not None else "unknown"
    accepted = accept_magic_link_request(
        settings.database_url,
        email,
        ip_address,
        settings.magic_link_email_hourly_limit,
        settings.magic_link_ip_hourly_limit,
    )
    if not accepted:
        raise HTTPException(status_code=429)
    token = issue_magic_link(
        settings.database_url, email, settings.magic_link_ttl_seconds
    )
    if token is not None and settings.environment != "production":
        context.development_outbox.append(
            {"to": email, "magic_link": f"/tutor/sign-in/confirm?token={token}"}
        )
    return MagicLinkAcceptedResponse(
        status="accepted",
        message="If the address is eligible, a sign-in link has been sent.",
    )


@router.get("/api/development/outbox")
async def development_outbox(request: Request) -> dict[str, list[dict[str, str]]]:
    context = context_from(request)
    if context.settings.environment == "production":
        raise HTTPException(status_code=404)
    return {"messages": context.development_outbox}


@router.get("/api/auth/magic-links/confirm")
async def inspect_magic_link(token: str, request: Request) -> dict[str, str]:
    if not magic_link_is_active(context_from(request).settings.database_url, token):
        raise HTTPException(status_code=400)
    return {"status": "confirmation_required"}


@router.post("/api/auth/magic-links/confirm")
async def confirm_magic_link(
    confirmation: MagicLinkConfirmation, request: Request, response: Response
) -> dict[str, str]:
    context = context_from(request)
    settings = context.settings
    authenticated = consume_magic_link(
        settings.database_url,
        confirmation.token,
        settings.session_inactivity_seconds,
        settings.session_absolute_seconds,
        request.cookies.get(context.session_cookie_name),
    )
    if authenticated is None:
        raise HTTPException(status_code=400)
    raw_session, raw_csrf, role = authenticated
    set_session_cookies(response, context, raw_session, raw_csrf)
    return {"status": "authenticated", "role": role, "csrf_token": raw_csrf}
