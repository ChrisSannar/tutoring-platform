from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from starlette.exceptions import HTTPException

from starlette.responses import JSONResponse, Response

def install_error_handling(application: FastAPI) -> None:
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
            code, message = "not_found", "Resource not found"
        else:
            code, message = "request_failed", "Request failed"
        return JSONResponse(
            status_code=exception.status_code,
            content={
                "code": code,
                "message": message,
                "request_id": request.state.request_id,
            },
        )

    @application.exception_handler(RequestValidationError)
    async def sanitized_validation_error(
        request: Request, _exception: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "request_failed",
                "message": "Request failed",
                "request_id": request.state.request_id,
            },
        )
