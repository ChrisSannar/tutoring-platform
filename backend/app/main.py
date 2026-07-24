from fastapi import FastAPI

from app.application_context import ApplicationContext
from app.http import install_error_handling
from app.routes.auth import router as auth_router
from app.routes.bookings import router as booking_router
from app.routes.checkout import router as checkout_router
from app.routes.invitations import router as invitation_router
from app.routes.lesson_notes import router as lesson_note_router
from app.routes.system import router as system_router
from app.routes.tutor import router as tutor_router


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
    application.include_router(checkout_router)
    return application


app = create_app()
