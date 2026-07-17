from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.http.security import require_mutation, require_session
from app.login_requests import active_login_requests, dismiss_login_request, generate_login_link
from app.models.login_requests import GeneratedLoginLinkResponse, LoginRequestListResponse

router = APIRouter(prefix="/api/tutor/login-requests")


@router.get("", response_model=LoginRequestListResponse)
async def list_login_requests(request: Request) -> dict[str, object]:
    require_session(request, "tutor")
    return {"login_requests": active_login_requests(context_from(request).settings.database_url)}


@router.post("/{request_id}/magic-link", status_code=201, response_model=GeneratedLoginLinkResponse)
async def create_login_link(request_id: str, request: Request) -> dict[str, str]:
    require_mutation(request, "tutor")
    settings = context_from(request).settings
    token = generate_login_link(settings.database_url, request_id, settings.magic_link_ttl_seconds)
    if token is None:
        raise HTTPException(status_code=409)
    return {"magic_link": f"/sign-in/confirm?token={token}"}


@router.delete("/{request_id}", status_code=204)
async def dismiss(request_id: str, request: Request) -> None:
    require_mutation(request, "tutor")
    if not dismiss_login_request(context_from(request).settings.database_url, request_id):
        raise HTTPException(status_code=404)
