from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.http.security import require_mutation

router = APIRouter()


class TestClockInput(BaseModel):
    now: datetime


@router.post("/api/testing/clock")
async def set_test_clock(submission: TestClockInput, request: Request):
    require_mutation(request, "tutor")
    context = context_from(request)
    if context.settings.environment != "test":
        raise HTTPException(status_code=404)
    context.now = lambda: submission.now
    return {"now": submission.now}
