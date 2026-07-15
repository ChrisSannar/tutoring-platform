from datetime import datetime
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, Header, Request
from pydantic import BaseModel, Field, field_validator
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.database import readiness_status
from app.invitations import (
    InvitationClaimConflict,
    activate_invitation,
    claim_invitation,
    correct_invitation_email,
    create_draft_invitation,
    get_active_invitation_by_token,
    get_active_invitation_claim,
    get_tutor_invitation,
    issue_invitation_claim_token,
    regenerate_invitation,
    revoke_invitation,
)
from app.session_requests import (
    create_session_request,
    get_session_request,
    list_business_session_requests,
)
from app.authentication import (
    accept_magic_link_request,
    active_session,
    consume_magic_link,
    issue_magic_link,
    magic_link_is_active,
    revoke_session,
    session_authorizes_mutation,
    student_session_details,
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


class InvitationDraftRequest(BaseModel):
    email: str
    display_name: str
    shared_personal_message: str
    private_tutor_note: str


class TutorInvitationResponse(BaseModel):
    id: str
    email: str
    display_name: str
    shared_personal_message: str
    private_tutor_note: str
    status: Literal["draft"]


class ActivatedInvitationResponse(BaseModel):
    id: str
    status: Literal["active"]
    invitation_url: str
    expires_at: datetime


class TutorInvitationRecordResponse(BaseModel):
    id: str
    email: str
    display_name: str
    shared_personal_message: str
    private_tutor_note: str
    status: Literal["draft", "active", "claimed", "revoked", "expired"]
    expires_at: datetime | None


class InviteeInvitationResponse(BaseModel):
    email: str
    display_name: str
    shared_personal_message: str


class InvitationEmailCorrectionRequest(BaseModel):
    email: str


class InvitationClaimLinkRequest(BaseModel):
    email: str


class InvitationClaimConfirmationResponse(BaseModel):
    status: Literal["confirmation_required"]
    email: str
    display_name: str


class InvitationClaimConfirmationRequest(BaseModel):
    token: str
    display_name: str


class ClaimedInvitationResponse(BaseModel):
    status: Literal["claimed"]
    role: Literal["student"]
    email: str
    display_name: str
    csrf_token: str


class CorrectedInvitationResponse(BaseModel):
    id: str
    email: str
    status: Literal["draft", "active"]


class RevokedInvitationResponse(BaseModel):
    id: str
    status: Literal["revoked"]


class SessionRequestSubmission(BaseModel):
    service: str
    preferred_start: datetime
    timezone: str
    message: str | None = Field(default=None, max_length=1000)

    @field_validator("timezone")
    @classmethod
    def require_iana_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("timezone must be an IANA timezone") from error
        return value


class SessionRequestResponse(BaseModel):
    id: str
    service: str
    preferred_start: datetime
    timezone: str
    message: str | None
    status: Literal["pending"]


class SessionRequestStudentResponse(BaseModel):
    email: str
    display_name: str


class TutorSessionRequestResponse(SessionRequestResponse):
    student: SessionRequestStudentResponse


class TutorSessionRequestListResponse(BaseModel):
    requests: list[TutorSessionRequestResponse]


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
            settings.database_url,
            normalized_email,
            ip_address,
            settings.magic_link_email_hourly_limit,
            settings.magic_link_ip_hourly_limit,
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

    @application.get("/api/student/session")
    async def get_student_session(request: Request) -> dict[str, str]:
        raw_session = request.cookies.get(session_cookie_name)
        if raw_session is None or active_session(
            settings.database_url,
            raw_session,
            settings.session_inactivity_seconds,
        ) != "student":
            raise HTTPException(status_code=401)
        student = student_session_details(settings.database_url, raw_session)
        if student is None:
            raise HTTPException(status_code=401)
        return student

    @application.post(
        "/api/tutor/invitations",
        status_code=201,
        response_model=TutorInvitationResponse,
    )
    async def create_invitation(
        invitation: InvitationDraftRequest,
        request: Request,
    ) -> TutorInvitationResponse:
        raw_session = request.cookies.get(session_cookie_name)
        raw_csrf = request.headers.get("x-csrf-token")
        if (
            raw_session is None
            or raw_csrf is None
            or not session_authorizes_mutation(
                settings.database_url,
                raw_session,
                raw_csrf,
                "tutor",
            )
        ):
            raise HTTPException(status_code=401 if raw_session is None else 403)
        if request.headers.get("origin") != settings.application_origin:
            raise HTTPException(status_code=403)
        return TutorInvitationResponse.model_validate(
            create_draft_invitation(
                settings.database_url,
                invitation.email,
                invitation.display_name,
                invitation.shared_personal_message,
                invitation.private_tutor_note,
            )
        )

    @application.post(
        "/api/student/session-requests",
        status_code=201,
        response_model=SessionRequestResponse,
    )
    async def submit_session_request(
        submission: SessionRequestSubmission,
        request: Request,
        idempotency_key: str = Header(),
    ) -> SessionRequestResponse:
        raw_session = request.cookies.get(session_cookie_name)
        raw_csrf = request.headers.get("x-csrf-token")
        if raw_session is None or active_session(
            settings.database_url,
            raw_session,
            settings.session_inactivity_seconds,
        ) != "student":
            raise HTTPException(status_code=401)
        if raw_csrf is None:
            raise HTTPException(status_code=403)
        if not session_authorizes_mutation(
            settings.database_url, raw_session, raw_csrf, "student"
        ):
            raise HTTPException(status_code=403)
        if request.headers.get("origin") != settings.application_origin:
            raise HTTPException(status_code=403)
        return SessionRequestResponse.model_validate(
            create_session_request(
                settings.database_url,
                raw_session,
                idempotency_key,
                submission.service,
                submission.preferred_start,
                submission.timezone,
                submission.message,
            )
        )

    @application.get(
        "/api/student/session-requests/{session_request_id}",
        response_model=SessionRequestResponse,
    )
    async def view_student_session_request(
        session_request_id: str, request: Request
    ) -> SessionRequestResponse:
        raw_session = request.cookies.get(session_cookie_name)
        if raw_session is None or active_session(
            settings.database_url,
            raw_session,
            settings.session_inactivity_seconds,
        ) != "student":
            raise HTTPException(status_code=401)
        session_request = get_session_request(
            settings.database_url, raw_session, session_request_id
        )
        if session_request is None:
            raise HTTPException(status_code=404)
        return SessionRequestResponse.model_validate(session_request)

    @application.get(
        "/api/tutor/session-requests",
        response_model=TutorSessionRequestListResponse,
    )
    async def view_business_session_requests(
        request: Request,
    ) -> TutorSessionRequestListResponse:
        raw_session = request.cookies.get(session_cookie_name)
        if raw_session is None or active_session(
            settings.database_url,
            raw_session,
            settings.session_inactivity_seconds,
        ) != "tutor":
            raise HTTPException(status_code=401)
        return TutorSessionRequestListResponse.model_validate(
            {
                "requests": list_business_session_requests(
                    settings.database_url
                )
            }
        )

    @application.post(
        "/api/tutor/invitations/{invitation_id}/activate",
        response_model=ActivatedInvitationResponse,
    )
    async def activate_draft_invitation(
        invitation_id: str, request: Request
    ) -> ActivatedInvitationResponse:
        raw_session = request.cookies.get(session_cookie_name)
        raw_csrf = request.headers.get("x-csrf-token")
        if (
            raw_session is None
            or raw_csrf is None
            or not session_authorizes_mutation(
                settings.database_url, raw_session, raw_csrf, "tutor"
            )
        ):
            raise HTTPException(status_code=401 if raw_session is None else 403)
        if request.headers.get("origin") != settings.application_origin:
            raise HTTPException(status_code=403)
        activated = activate_invitation(
            settings.database_url,
            invitation_id,
            settings.invitation_ttl_seconds,
        )
        if activated is None:
            raise HTTPException(status_code=404)
        return ActivatedInvitationResponse.model_validate(activated)

    @application.get(
        "/api/tutor/invitations/{invitation_id}",
        response_model=TutorInvitationRecordResponse,
    )
    async def inspect_tutor_invitation(
        invitation_id: str, request: Request
    ) -> TutorInvitationRecordResponse:
        raw_session = request.cookies.get(session_cookie_name)
        if raw_session is None or active_session(
            settings.database_url,
            raw_session,
            settings.session_inactivity_seconds,
        ) != "tutor":
            raise HTTPException(status_code=401)
        invitation = get_tutor_invitation(settings.database_url, invitation_id)
        if invitation is None:
            raise HTTPException(status_code=404)
        return TutorInvitationRecordResponse.model_validate(invitation)

    @application.patch(
        "/api/tutor/invitations/{invitation_id}",
        response_model=CorrectedInvitationResponse,
    )
    async def correct_bound_email(
        invitation_id: str,
        correction: InvitationEmailCorrectionRequest,
        request: Request,
    ) -> CorrectedInvitationResponse:
        raw_session = request.cookies.get(session_cookie_name)
        raw_csrf = request.headers.get("x-csrf-token")
        if (
            raw_session is None
            or raw_csrf is None
            or not session_authorizes_mutation(
                settings.database_url, raw_session, raw_csrf, "tutor"
            )
        ):
            raise HTTPException(status_code=401 if raw_session is None else 403)
        if request.headers.get("origin") != settings.application_origin:
            raise HTTPException(status_code=403)
        corrected = correct_invitation_email(
            settings.database_url, invitation_id, correction.email
        )
        if corrected is None:
            raise HTTPException(status_code=404)
        return CorrectedInvitationResponse.model_validate(corrected)

    @application.post(
        "/api/tutor/invitations/{invitation_id}/revoke",
        response_model=RevokedInvitationResponse,
    )
    async def revoke_active_invitation(
        invitation_id: str, request: Request
    ) -> RevokedInvitationResponse:
        raw_session = request.cookies.get(session_cookie_name)
        raw_csrf = request.headers.get("x-csrf-token")
        if (
            raw_session is None
            or raw_csrf is None
            or not session_authorizes_mutation(
                settings.database_url, raw_session, raw_csrf, "tutor"
            )
        ):
            raise HTTPException(status_code=401 if raw_session is None else 403)
        if request.headers.get("origin") != settings.application_origin:
            raise HTTPException(status_code=403)
        revoked = revoke_invitation(settings.database_url, invitation_id)
        if revoked is None:
            raise HTTPException(status_code=404)
        return RevokedInvitationResponse.model_validate(revoked)

    @application.post(
        "/api/tutor/invitations/{invitation_id}/regenerate",
        response_model=ActivatedInvitationResponse,
    )
    async def regenerate_active_invitation(
        invitation_id: str, request: Request
    ) -> ActivatedInvitationResponse:
        raw_session = request.cookies.get(session_cookie_name)
        raw_csrf = request.headers.get("x-csrf-token")
        if (
            raw_session is None
            or raw_csrf is None
            or not session_authorizes_mutation(
                settings.database_url, raw_session, raw_csrf, "tutor"
            )
        ):
            raise HTTPException(status_code=401 if raw_session is None else 403)
        if request.headers.get("origin") != settings.application_origin:
            raise HTTPException(status_code=403)
        regenerated = regenerate_invitation(
            settings.database_url, invitation_id, settings.invitation_ttl_seconds
        )
        if regenerated is None:
            raise HTTPException(status_code=404)
        return ActivatedInvitationResponse.model_validate(regenerated)

    @application.get(
        "/api/invitations/{token}", response_model=InviteeInvitationResponse
    )
    @application.get("/invite/{token}", response_model=InviteeInvitationResponse)
    async def open_invitation(token: str) -> InviteeInvitationResponse:
        invitation = get_active_invitation_by_token(settings.database_url, token)
        if invitation is None:
            raise HTTPException(status_code=404)
        return InviteeInvitationResponse.model_validate(invitation)

    @application.post(
        "/api/invitations/{token}/magic-links",
        status_code=202,
        response_model=MagicLinkAcceptedResponse,
    )
    async def request_invitation_claim_link(
        token: str, claim_request: InvitationClaimLinkRequest
    ) -> MagicLinkAcceptedResponse:
        normalized_email = claim_request.email.strip().lower()
        claim_token = issue_invitation_claim_token(
            settings.database_url,
            token,
            normalized_email,
            settings.magic_link_ttl_seconds,
        )
        if claim_token is not None and settings.environment != "production":
            development_outbox.append(
                {
                    "to": normalized_email,
                    "magic_link": f"/student/claim/confirm?token={claim_token}",
                }
            )
        return MagicLinkAcceptedResponse(
            status="accepted",
            message="If the address matches, a verification link has been sent.",
        )

    @application.get(
        "/api/invitation-claims/confirm",
        response_model=InvitationClaimConfirmationResponse,
    )
    async def inspect_invitation_claim(
        token: str,
    ) -> InvitationClaimConfirmationResponse:
        invitation = get_active_invitation_claim(settings.database_url, token)
        if invitation is None:
            raise HTTPException(status_code=400)
        return InvitationClaimConfirmationResponse(
            status="confirmation_required",
            email=invitation["email"],
            display_name=invitation["display_name"],
        )

    @application.post(
        "/api/invitation-claims/confirm",
        response_model=ClaimedInvitationResponse,
    )
    async def confirm_invitation_claim(
        confirmation: InvitationClaimConfirmationRequest,
        request: Request,
        response: Response,
    ) -> ClaimedInvitationResponse:
        try:
            claimed = claim_invitation(
                settings.database_url,
                confirmation.token,
                confirmation.display_name,
                settings.session_inactivity_seconds,
                settings.session_absolute_seconds,
                request.cookies.get(session_cookie_name),
            )
        except InvitationClaimConflict:
            raise HTTPException(status_code=409) from None
        if claimed is None:
            raise HTTPException(status_code=400)
        response.set_cookie(
            key=session_cookie_name,
            value=claimed["session"],
            secure=settings.environment == "production",
            httponly=True,
            samesite="lax",
            path="/",
            max_age=90 * 24 * 60 * 60,
        )
        response.set_cookie(
            key=csrf_cookie_name,
            value=claimed["csrf_token"],
            secure=settings.environment == "production",
            httponly=False,
            samesite="strict",
            path="/",
            max_age=90 * 24 * 60 * 60,
        )
        return ClaimedInvitationResponse.model_validate(claimed)

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
