from fastapi import APIRouter, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.http.security import require_session
from app.models.students import TutorStudentDetailResponse, TutorStudentListResponse
from app.students import get_student_detail, list_students

router = APIRouter()


@router.get("/api/tutor/students", response_model=TutorStudentListResponse)
async def view_students(request: Request) -> TutorStudentListResponse:
    require_session(request, "tutor")
    students = list_students(context_from(request).settings.database_url)
    return TutorStudentListResponse.model_validate({"students": students})


@router.get(
    "/api/tutor/students/{student_id}", response_model=TutorStudentDetailResponse
)
async def view_student_detail(
    student_id: str, request: Request
) -> TutorStudentDetailResponse:
    require_session(request, "tutor")
    student = get_student_detail(
        context_from(request).settings.database_url, student_id
    )
    if student is None:
        raise HTTPException(status_code=404)
    return TutorStudentDetailResponse.model_validate(student)
