from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.database import readiness_status


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadyResponse(BaseModel):
    status: Literal["ready"]


def create_app() -> FastAPI:
    settings = get_settings()
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

    return application


app = create_app()
