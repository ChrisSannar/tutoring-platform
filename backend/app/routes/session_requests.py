from fastapi import APIRouter

from app.routes.student_session_requests import router as student_router
from app.routes.tutor_session_requests import router as tutor_router

router = APIRouter()
router.include_router(student_router)
router.include_router(tutor_router)
