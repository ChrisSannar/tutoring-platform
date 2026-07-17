from fastapi import FastAPI

from app.application_context import ApplicationContext
from app.http.errors import install_error_handling
from app.routes.auth import router as auth_router
from app.routes.invitation_claims import router as invitation_claim_router
from app.routes.inquiries import router as inquiry_router
from app.routes.invitee_invitations import router as invitee_invitation_router
from app.routes.pilot_data import router as pilot_data_router
from app.routes.session_requests import router as session_request_router
from app.routes.system import router as system_router
from app.routes.tutor_invitations import router as tutor_invitation_router
from app.routes.tutor_inquiries import router as tutor_inquiry_router


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
    application.include_router(inquiry_router)
    application.include_router(tutor_invitation_router)
    application.include_router(tutor_inquiry_router)
    application.include_router(invitee_invitation_router)
    application.include_router(invitation_claim_router)
    application.include_router(session_request_router)
    application.include_router(pilot_data_router)
    return application


app = create_app()
