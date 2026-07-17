from fastapi import APIRouter, Request

from app.availability import create_blocked_time, create_window, list_windows
from app.http.context import context_from
from app.http.security import require_mutation, require_session
from app.models.availability import AvailabilityWindowInput, AvailabilityWindowResponse, BlockedTimeInput, BlockedTimeResponse

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
