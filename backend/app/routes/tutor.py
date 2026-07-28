from fastapi import APIRouter, Header, Request
from starlette.exceptions import HTTPException

from app.availability import create_blocked_time, create_override, create_window, delete_blocked_time, delete_override, delete_window, list_blocked_times, list_overrides, list_windows, update_blocked_time, update_override, update_window
from app.funding import CreditAdjustmentConflict, adjust_session_credits, list_credit_ledger
from app.http import context_from, require_mutation, require_session
from app.login_requests import active_login_requests, dismiss_login_request, generate_login_link
from app.models import (
    AvailabilityWindowInput,
    AvailabilityWindowResponse,
    BlockedTimeInput,
    BlockedTimeResponse,
    CreditAdjustmentRequest,
    CreditBalanceResponse,
    CreditLedgerResponse,
    GeneratedLoginLinkResponse,
    LoginRequestListResponse,
    PilotDataDeletionRequest,
    PilotDataDeletionResponse,
    TutorOverrideInput,
    TutorOverrideResponse,
    TutorSettingsResponse,
    TutorSettingsUpdate,
    TutorStudentDetailResponse,
    TutorStudentListResponse,
)
from app.pilot_data import delete_student_pilot_data
from app.students import get_student_detail, list_students
from app.tutor_settings import get_tutor_settings, update_tutor_settings

router = APIRouter()


@router.get("/api/tutor/availability-windows", response_model=list[AvailabilityWindowResponse])
async def get_windows(request: Request):
    require_session(request, "tutor")
    return list_windows(context_from(request).settings.database_url)


@router.post("/api/tutor/availability-windows", status_code=201, response_model=AvailabilityWindowResponse)
async def add_window(submission: AvailabilityWindowInput, request: Request):
    require_mutation(request, "tutor")
    return create_window(context_from(request).settings.database_url, submission.weekday, submission.start_time, submission.end_time)


@router.post("/api/tutor/blocked-times", status_code=201, response_model=BlockedTimeResponse)
async def add_blocked_time(submission: BlockedTimeInput, request: Request):
    require_mutation(request, "tutor")
    return create_blocked_time(context_from(request).settings.database_url, submission.start_at, submission.end_at, submission.reason)


@router.put("/api/tutor/availability-windows/{window_id}", response_model=AvailabilityWindowResponse)
async def replace_window(window_id: str, submission: AvailabilityWindowInput, request: Request):
    require_mutation(request, "tutor")
    result = update_window(context_from(request).settings.database_url, window_id, submission.weekday, submission.start_time, submission.end_time)
    if result is None: raise HTTPException(status_code=404)
    return result


@router.delete("/api/tutor/availability-windows/{window_id}", status_code=204)
async def remove_window(window_id: str, request: Request):
    require_mutation(request, "tutor")
    if not delete_window(context_from(request).settings.database_url, window_id): raise HTTPException(status_code=404)


@router.get("/api/tutor/blocked-times", response_model=list[BlockedTimeResponse])
async def get_blocked_times(request: Request):
    require_session(request, "tutor")
    return list_blocked_times(context_from(request).settings.database_url)


@router.put("/api/tutor/blocked-times/{blocked_id}", response_model=BlockedTimeResponse)
async def replace_blocked_time(blocked_id: str, submission: BlockedTimeInput, request: Request):
    require_mutation(request, "tutor")
    result = update_blocked_time(context_from(request).settings.database_url, blocked_id, submission.start_at, submission.end_at, submission.reason)
    if result is None: raise HTTPException(status_code=404)
    return result


@router.delete("/api/tutor/blocked-times/{blocked_id}", status_code=204)
async def remove_blocked_time(blocked_id: str, request: Request):
    require_mutation(request, "tutor")
    if not delete_blocked_time(context_from(request).settings.database_url, blocked_id): raise HTTPException(status_code=404)


@router.post("/api/tutor/overrides", status_code=201, response_model=TutorOverrideResponse)
async def add_override(submission: TutorOverrideInput, request: Request):
    require_mutation(request, "tutor")
    return create_override(context_from(request).settings.database_url, submission.start_at, submission.warning)


@router.get("/api/tutor/overrides", response_model=list[TutorOverrideResponse])
async def get_overrides(request: Request):
    require_session(request, "tutor")
    return list_overrides(context_from(request).settings.database_url)


@router.put("/api/tutor/overrides/{override_id}", response_model=TutorOverrideResponse)
async def replace_override(override_id: str, submission: TutorOverrideInput, request: Request):
    require_mutation(request, "tutor")
    result = update_override(context_from(request).settings.database_url, override_id, submission.start_at, submission.warning)
    if result is None: raise HTTPException(status_code=404)
    return result


@router.delete("/api/tutor/overrides/{override_id}", status_code=204)
async def remove_override(override_id: str, request: Request):
    require_mutation(request, "tutor")
    if not delete_override(context_from(request).settings.database_url, override_id): raise HTTPException(status_code=404)


@router.post(
    "/api/tutor/students/{student_id}/credits",
    response_model=CreditBalanceResponse,
)
async def adjust_student_credits(
    student_id: str,
    adjustment: CreditAdjustmentRequest,
    request: Request,
    idempotency_key: str = Header(),
) -> CreditBalanceResponse:
    require_mutation(request, "tutor")
    try:
        balance = adjust_session_credits(
            context_from(request).settings.database_url,
            student_id,
            adjustment.quantity,
            adjustment.reason,
            idempotency_key,
            context_from(request).now(),
        )
    except CreditAdjustmentConflict:
        raise HTTPException(status_code=409) from None
    return CreditBalanceResponse.model_validate(balance)


@router.get(
    "/api/tutor/students/{student_id}/credit-ledger",
    response_model=CreditLedgerResponse,
)
async def view_student_credit_ledger(
    student_id: str, request: Request
) -> CreditLedgerResponse:
    require_session(request, "tutor")
    events = list_credit_ledger(
        context_from(request).settings.database_url,
        student_id,
        context_from(request).now(),
    )
    if events is None:
        raise HTTPException(status_code=404)
    return CreditLedgerResponse.model_validate({"events": events})


@router.get("/api/tutor/login-requests", response_model=LoginRequestListResponse)
async def list_login_requests(request: Request) -> dict[str, object]:
    require_session(request, "tutor")
    return {"login_requests": active_login_requests(context_from(request).settings.database_url)}


@router.post("/api/tutor/login-requests/{request_id}/magic-link", status_code=201, response_model=GeneratedLoginLinkResponse)
async def create_login_link(request_id: str, request: Request) -> dict[str, str]:
    require_mutation(request, "tutor")
    settings = context_from(request).settings
    token = generate_login_link(settings.database_url, request_id, settings.magic_link_ttl_seconds)
    if token is None:
        raise HTTPException(status_code=409)
    return {"magic_link": f"/sign-in/confirm?token={token}"}


@router.delete("/api/tutor/login-requests/{request_id}", status_code=204)
async def dismiss(request_id: str, request: Request) -> None:
    require_mutation(request, "tutor")
    if not dismiss_login_request(context_from(request).settings.database_url, request_id):
        raise HTTPException(status_code=404)


@router.get("/api/tutor/settings", response_model=TutorSettingsResponse)
async def view_tutor_settings(request: Request) -> TutorSettingsResponse:
    require_session(request, "tutor")
    settings = get_tutor_settings(context_from(request).settings.database_url)
    return TutorSettingsResponse.model_validate(settings)


@router.put("/api/tutor/settings", response_model=TutorSettingsResponse)
async def replace_tutor_settings(
    update: TutorSettingsUpdate, request: Request
) -> TutorSettingsResponse:
    require_mutation(request, "tutor")
    settings = update_tutor_settings(
        context_from(request).settings.database_url,
        update.tutor_timezone,
        update.default_meeting_details,
    )
    return TutorSettingsResponse.model_validate(settings)


@router.get("/api/tutor/students", response_model=TutorStudentListResponse)
async def view_students(request: Request) -> TutorStudentListResponse:
    require_session(request, "tutor")
    students = list_students(context_from(request).settings.database_url)
    return TutorStudentListResponse.model_validate({"students": students})


@router.get(
    "/api/tutor/students/{student_id}", response_model=TutorStudentDetailResponse
)
async def view_student_detail(
    student_id: str, request: Request
) -> TutorStudentDetailResponse:
    require_session(request, "tutor")
    student = get_student_detail(
        context_from(request).settings.database_url,
        student_id,
        context_from(request).now(),
    )
    if student is None:
        raise HTTPException(status_code=404)
    return TutorStudentDetailResponse.model_validate(student)


@router.delete(
    "/api/tutor/students/{student_account_id}/pilot-data",
    response_model=PilotDataDeletionResponse,
)
async def delete_collected_pilot_data(
    student_account_id: str,
    deletion: PilotDataDeletionRequest,
    request: Request,
) -> PilotDataDeletionResponse:
    require_mutation(request, "tutor")
    if deletion.confirmation != "DELETE COLLECTED DATA":
        raise HTTPException(status_code=400)
    removed = delete_student_pilot_data(
        context_from(request).settings.database_url, student_account_id
    )
    if removed is None:
        raise HTTPException(status_code=404)
    return PilotDataDeletionResponse.model_validate(
        {"status": "deleted", "removed": removed}
    )
