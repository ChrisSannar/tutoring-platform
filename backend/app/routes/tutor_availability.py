from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.availability import create_blocked_time, create_override, create_window, delete_blocked_time, delete_override, delete_window, list_blocked_times, list_overrides, list_windows, update_blocked_time, update_window
from app.http.context import context_from
from app.http.security import require_mutation, require_session
from app.models.availability import AvailabilityWindowInput, AvailabilityWindowResponse, BlockedTimeInput, BlockedTimeResponse, TutorOverrideInput, TutorOverrideResponse

router = APIRouter(prefix="/api/tutor")


@router.get("/availability-windows", response_model=list[AvailabilityWindowResponse])
async def get_windows(request: Request):
    require_session(request, "tutor")
    return list_windows(context_from(request).settings.database_url)


@router.post("/availability-windows", status_code=201, response_model=AvailabilityWindowResponse)
async def add_window(submission: AvailabilityWindowInput, request: Request):
    require_mutation(request, "tutor")
    return create_window(context_from(request).settings.database_url, submission.weekday, submission.start_time, submission.end_time)


@router.post("/blocked-times", status_code=201, response_model=BlockedTimeResponse)
async def add_blocked_time(submission: BlockedTimeInput, request: Request):
    require_mutation(request, "tutor")
    return create_blocked_time(context_from(request).settings.database_url, submission.start_at, submission.end_at, submission.reason)


@router.put("/availability-windows/{window_id}", response_model=AvailabilityWindowResponse)
async def replace_window(window_id: str, submission: AvailabilityWindowInput, request: Request):
    require_mutation(request, "tutor")
    result = update_window(context_from(request).settings.database_url, window_id, submission.weekday, submission.start_time, submission.end_time)
    if result is None: raise HTTPException(status_code=404)
    return result


@router.delete("/availability-windows/{window_id}", status_code=204)
async def remove_window(window_id: str, request: Request):
    require_mutation(request, "tutor")
    if not delete_window(context_from(request).settings.database_url, window_id): raise HTTPException(status_code=404)


@router.get("/blocked-times", response_model=list[BlockedTimeResponse])
async def get_blocked_times(request: Request):
    require_session(request, "tutor")
    return list_blocked_times(context_from(request).settings.database_url)


@router.put("/blocked-times/{blocked_id}", response_model=BlockedTimeResponse)
async def replace_blocked_time(blocked_id: str, submission: BlockedTimeInput, request: Request):
    require_mutation(request, "tutor")
    result = update_blocked_time(context_from(request).settings.database_url, blocked_id, submission.start_at, submission.end_at, submission.reason)
    if result is None: raise HTTPException(status_code=404)
    return result


@router.delete("/blocked-times/{blocked_id}", status_code=204)
async def remove_blocked_time(blocked_id: str, request: Request):
    require_mutation(request, "tutor")
    if not delete_blocked_time(context_from(request).settings.database_url, blocked_id): raise HTTPException(status_code=404)


@router.post("/overrides", status_code=201, response_model=TutorOverrideResponse)
async def add_override(submission: TutorOverrideInput, request: Request):
    require_mutation(request, "tutor")
    return create_override(context_from(request).settings.database_url, submission.start_at, submission.warning)


@router.get("/overrides", response_model=list[TutorOverrideResponse])
async def get_overrides(request: Request):
    require_session(request, "tutor")
    return list_overrides(context_from(request).settings.database_url)


@router.delete("/overrides/{override_id}", status_code=204)
async def remove_override(override_id: str, request: Request):
    require_mutation(request, "tutor")
    if not delete_override(context_from(request).settings.database_url, override_id): raise HTTPException(status_code=404)
