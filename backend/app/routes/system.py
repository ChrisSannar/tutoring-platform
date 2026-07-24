from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.database import readiness_status
from app.http import context_from, require_mutation

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadyResponse(BaseModel):
    status: Literal["ready"]


class TestClockInput(BaseModel):
    now: datetime


@router.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/api/ready", response_model=ReadyResponse)
async def ready(request: Request) -> ReadyResponse | JSONResponse:
    status = readiness_status(context_from(request).settings.database_url)
    if status == "ready":
        return ReadyResponse(status="ready")
    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "reason": status},
    )


@router.post("/api/testing/clock")
async def set_test_clock(submission: TestClockInput, request: Request):
    require_mutation(request, "tutor")
    context = context_from(request)
    if context.settings.environment != "test":
        raise HTTPException(status_code=404)
    context.now = lambda: submission.now
    return {"now": submission.now}
