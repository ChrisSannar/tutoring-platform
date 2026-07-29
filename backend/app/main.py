from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, Response
from starlette.staticfiles import StaticFiles

from app.application_context import ApplicationContext
from app.http import install_error_handling
from app.routes.auth import router as auth_router
from app.routes.bookings import router as booking_router
from app.routes.invitations import router as invitation_router
from app.routes.lesson_notes import router as lesson_note_router
from app.routes.system import router as system_router
from app.routes.tutor import router as tutor_router

FRONTEND_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=(), payment=()",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def create_app() -> FastAPI:
    context = ApplicationContext.build()
    application = FastAPI(
        title="Tutoring Platform",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.state.context = context
    install_error_handling(application)
    application.include_router(system_router)
    application.include_router(auth_router)
    application.include_router(invitation_router)
    application.include_router(tutor_router)
    application.include_router(booking_router)
    application.include_router(lesson_note_router)
    if context.settings.environment == "production":
        frontend_directory = Path("frontend/dist").resolve()

        @application.middleware("http")
        async def secure_frontend(request, call_next) -> Response:
            response = await call_next(request)
            if not request.url.path.startswith("/api"):
                response.headers.update(FRONTEND_HEADERS)
            return response

        application.mount(
            "/assets",
            StaticFiles(directory=frontend_directory / "assets"),
            name="frontend-assets",
        )

        @application.get("/{path:path}", include_in_schema=False)
        async def frontend(path: str) -> FileResponse:
            if path == "api" or path.startswith("api/"):
                raise HTTPException(status_code=404)
            asset = (frontend_directory / path).resolve()
            if asset.is_relative_to(frontend_directory) and asset.is_file():
                return FileResponse(asset)
            return FileResponse(frontend_directory / "index.html")

    return application


app = create_app()
