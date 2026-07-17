from fastapi import APIRouter, Request
from pydantic import BaseModel
from starlette.responses import JSONResponse
from typing import Literal

from app.database import readiness_status
from app.http.context import context_from

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadyResponse(BaseModel):
    status: Literal["ready"]


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
