from fastapi import APIRouter, Request

from app.http.context import context_from
from app.http.security import require_session
from app.models.students import TutorStudentListResponse
from app.students import list_students

router = APIRouter()


@router.get("/api/tutor/students", response_model=TutorStudentListResponse)
async def view_students(request: Request) -> TutorStudentListResponse:
    require_session(request, "tutor")
    students = list_students(context_from(request).settings.database_url)
    return TutorStudentListResponse.model_validate({"students": students})
