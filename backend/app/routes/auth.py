from fastapi import APIRouter

from app.routes.auth_magic_links import router as magic_link_router
from app.routes.auth_sessions import router as session_router

router = APIRouter()
router.include_router(magic_link_router)
router.include_router(session_router)
