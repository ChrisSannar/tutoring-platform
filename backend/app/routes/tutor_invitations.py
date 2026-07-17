from fastapi import APIRouter

from app.routes.tutor_invitation_lifecycle import router as lifecycle_router
from app.routes.tutor_invitation_links import router as links_router
from app.routes.tutor_invitation_records import router as records_router

router = APIRouter()
router.include_router(records_router)
router.include_router(lifecycle_router)
router.include_router(links_router)
