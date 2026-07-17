from fastapi import APIRouter, Request

from app.http.context import context_from
from app.http.security import require_mutation, require_session
from app.models.tutor_settings import TutorSettingsResponse, TutorSettingsUpdate
from app.tutor_settings import get_tutor_settings, update_tutor_settings

router = APIRouter()


@router.get("/api/tutor/settings", response_model=TutorSettingsResponse)
async def view_tutor_settings(request: Request) -> TutorSettingsResponse:
    require_session(request, "tutor")
    settings = get_tutor_settings(context_from(request).settings.database_url)
    return TutorSettingsResponse.model_validate(settings)


@router.put("/api/tutor/settings", response_model=TutorSettingsResponse)
async def replace_tutor_settings(
    update: TutorSettingsUpdate, request: Request
) -> TutorSettingsResponse:
    require_mutation(request, "tutor")
    settings = update_tutor_settings(
        context_from(request).settings.database_url,
        update.currency,
        update.session_price_cents,
        update.tutor_timezone,
        update.default_meeting_details,
    )
    return TutorSettingsResponse.model_validate(settings)
