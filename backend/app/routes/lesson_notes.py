from fastapi import APIRouter, Request, Response
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.http.security import require_mutation, require_session
from app.lesson_notes import delete_note, download_note, publish_note, save_note, shared_notes, tutor_note_workspace, tutor_student_notes
from app.models.lesson_notes import ConfirmedLessonNoteDeletion, LessonNoteInput, LessonNoteResponse, SharedLessonNoteList, TutorLessonNoteWorkspaceItem

router = APIRouter()


@router.put("/api/tutor/bookings/{booking_id}/lesson-note", response_model=LessonNoteResponse)
async def save_lesson_note(booking_id: str, submission: LessonNoteInput, request: Request):
    require_mutation(request, "tutor")
    context = context_from(request)
    result = save_note(context.settings.database_url, booking_id, submission.title, submission.markdown_source, context.now())
    if result is None: raise HTTPException(status_code=409)
    return result


@router.post("/api/tutor/bookings/{booking_id}/lesson-note/publish", response_model=LessonNoteResponse)
async def publish_lesson_note(booking_id: str, request: Request):
    require_mutation(request, "tutor")
    context = context_from(request)
    result = publish_note(context.settings.database_url, booking_id, context.now())
    if result is None: raise HTTPException(status_code=404)
    return result


@router.delete("/api/tutor/bookings/{booking_id}/lesson-note", status_code=204)
async def remove_lesson_note(booking_id: str, submission: ConfirmedLessonNoteDeletion, request: Request):
    require_mutation(request, "tutor")
    context = context_from(request)
    if not delete_note(context.settings.database_url, booking_id, context.now()): raise HTTPException(status_code=404)


@router.get("/api/tutor/students/{student_id}/lesson-notes", response_model=list[LessonNoteResponse])
async def list_tutor_notes(student_id: str, request: Request):
    require_session(request, "tutor")
    return tutor_student_notes(context_from(request).settings.database_url, student_id)


@router.get("/api/tutor/students/{student_id}/lesson-note-workspace", response_model=list[TutorLessonNoteWorkspaceItem])
async def lesson_note_workspace(student_id: str, request: Request):
    require_session(request, "tutor")
    context = context_from(request)
    return tutor_note_workspace(context.settings.database_url, student_id, context.now())


@router.get("/api/student/lesson-notes", response_model=SharedLessonNoteList)
async def list_shared_notes(request: Request):
    raw_session = require_session(request, "student")
    return {"lesson_notes": shared_notes(context_from(request).settings.database_url, raw_session)}


@router.get("/api/student/lesson-notes/{booking_id}/download")
async def download_lesson_note(booking_id: str, request: Request):
    raw_session = require_session(request, "student")
    result = download_note(context_from(request).settings.database_url, raw_session, booking_id)
    if result is None: raise HTTPException(status_code=404)
    filename, source = result
    return Response(content=source, media_type="text/markdown", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
