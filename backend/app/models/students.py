from pydantic import BaseModel


class TutorStudentResponse(BaseModel):
    id: str
    email: str
    display_name: str


class TutorStudentListResponse(BaseModel):
    students: list[TutorStudentResponse]
