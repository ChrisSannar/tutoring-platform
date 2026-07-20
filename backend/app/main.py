from fastapi import FastAPI

from app.application_context import ApplicationContext
from app.http.errors import install_error_handling
from app.routes.auth import router as auth_router
from app.routes.direct_invitation_claims import router as direct_claim_router
from app.routes.inquiries import router as inquiry_router
from app.routes.invitee_invitations import router as invitee_invitation_router
from app.routes.pilot_data import router as pilot_data_router
from app.routes.system import router as system_router
from app.routes.tutor_invitations import router as tutor_invitation_router
from app.routes.tutor_students import router as tutor_student_router
from app.routes.tutor_settings import router as tutor_settings_router
from app.routes.tutor_inquiries import router as tutor_inquiry_router
from app.routes.tutor_credit_ledger import router as tutor_credit_router
from app.routes.tutor_login_requests import router as tutor_login_request_router
from app.routes.tutor_availability import router as tutor_availability_router
from app.routes.student_availability import router as student_availability_router
from app.routes.bookings import router as booking_router
from app.routes.lesson_notes import router as lesson_note_router
from app.routes.checkout import router as checkout_router
from app.routes.refunds import router as refund_router
from app.routes.testing import router as testing_router


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
    application.include_router(direct_claim_router)
    application.include_router(inquiry_router)
    application.include_router(tutor_invitation_router)
    application.include_router(tutor_student_router)
    application.include_router(tutor_settings_router)
    application.include_router(tutor_inquiry_router)
    application.include_router(tutor_credit_router)
    application.include_router(tutor_login_request_router)
    application.include_router(tutor_availability_router)
    application.include_router(student_availability_router)
    application.include_router(booking_router)
    application.include_router(lesson_note_router)
    application.include_router(checkout_router)
    application.include_router(refund_router)
    application.include_router(testing_router)
    application.include_router(invitee_invitation_router)
    application.include_router(pilot_data_router)
    return application


app = create_app()
