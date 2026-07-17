from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.models.pilot_data import PilotDataDeletionRequest, PilotDataDeletionResponse
from app.pilot_data import delete_student_pilot_data
from app.http.security import require_mutation

router = APIRouter()


@router.delete(
    "/api/tutor/students/{student_account_id}/pilot-data",
    response_model=PilotDataDeletionResponse,
)
async def delete_collected_pilot_data(
    student_account_id: str,
    deletion: PilotDataDeletionRequest,
    request: Request,
) -> PilotDataDeletionResponse:
    require_mutation(request, "tutor")
    if deletion.confirmation != "DELETE COLLECTED DATA":
        raise HTTPException(status_code=400)
    removed = delete_student_pilot_data(
        context_from(request).settings.database_url, student_account_id
    )
    if removed is None:
        raise HTTPException(status_code=404)
    return PilotDataDeletionResponse.model_validate(
        {"status": "deleted", "removed": removed}
    )
