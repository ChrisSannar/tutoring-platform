from fastapi import APIRouter, Request

from app.availability import derive_bookable_slots
from app.http.context import context_from
from app.http.security import require_session
from app.models.availability import BookableSlotList

router = APIRouter()


@router.get("/api/student/bookable-slots", response_model=BookableSlotList)
async def bookable_slots(request: Request):
    require_session(request, "student")
    context = context_from(request)
    timezone_name, slots = derive_bookable_slots(context.settings.database_url, context.now())
    return {"tutor_timezone": timezone_name, "slots": slots}
