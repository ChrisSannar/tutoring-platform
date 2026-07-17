from fastapi import APIRouter, Header, Request, Response
from starlette.exceptions import HTTPException

from app.bookings import booking_calendar_export, cancel_student_booking, create_complimentary_booking, create_student_booking, move_booking, reschedule_student_booking, tutor_calendar, upcoming_booking, update_meeting_details
from app.http.context import context_from
from app.http.security import require_mutation, require_session
from app.models.bookings import BookingResponse, ComplimentaryBookingInput, MeetingDetailsUpdate, StudentBookingCancellation, StudentBookingInput, StudentBookingMove, TutorBookingMove, TutorCalendarResponse

router = APIRouter()


@router.post("/api/student/bookings", status_code=201, response_model=BookingResponse)
async def student_booking(submission: StudentBookingInput, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    raw_session = require_mutation(request, "student")
    context = context_from(request)
    result = create_student_booking(context.settings.database_url, raw_session, submission.start_at, submission.focus, idempotency_key, context.now())
    if result is None: raise HTTPException(status_code=409)
    return result


@router.get("/api/student/bookings/upcoming", response_model=BookingResponse)
async def student_upcoming_booking(request: Request):
    raw_session = require_session(request, "student")
    result = upcoming_booking(context_from(request).settings.database_url, raw_session)
    if result is None: raise HTTPException(status_code=404)
    return result


@router.post("/api/tutor/students/{student_id}/bookings", status_code=201, response_model=BookingResponse)
async def complimentary_booking(student_id: str, submission: ComplimentaryBookingInput, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    require_mutation(request, "tutor")
    context = context_from(request)
    result = create_complimentary_booking(context.settings.database_url, student_id, submission.start_at, submission.focus, idempotency_key, context.now(), submission.override_id, submission.warning_acknowledged)
    if result is None: raise HTTPException(status_code=409)
    return result


@router.get("/api/tutor/bookings", response_model=TutorCalendarResponse)
async def tutor_bookings(request: Request):
    require_session(request, "tutor")
    return {"bookings": tutor_calendar(context_from(request).settings.database_url)}


@router.put("/api/tutor/bookings/{booking_id}/meeting-details", response_model=BookingResponse)
async def edit_meeting_details(booking_id: str, submission: MeetingDetailsUpdate, request: Request):
    require_mutation(request, "tutor")
    result = update_meeting_details(context_from(request).settings.database_url, booking_id, submission.meeting_details)
    if result is None: raise HTTPException(status_code=404)
    return result


@router.put("/api/tutor/bookings/{booking_id}/schedule", response_model=BookingResponse)
async def reschedule_booking(booking_id: str, submission: TutorBookingMove, request: Request):
    require_mutation(request, "tutor")
    context = context_from(request)
    result = move_booking(context.settings.database_url, booking_id, submission.start_at, context.now(), submission.override_id, submission.warning_acknowledged)
    if result is None: raise HTTPException(status_code=409)
    return result


@router.put("/api/student/bookings/{booking_id}/schedule", response_model=BookingResponse)
async def student_reschedule(booking_id: str, submission: StudentBookingMove, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    raw_session = require_mutation(request, "student")
    context = context_from(request)
    result = reschedule_student_booking(context.settings.database_url, raw_session, booking_id, submission.start_at, idempotency_key, context.now())
    if result is None: raise HTTPException(status_code=409)
    return result


@router.post("/api/student/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def student_cancel(booking_id: str, submission: StudentBookingCancellation, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    raw_session = require_mutation(request, "student")
    context = context_from(request)
    result = cancel_student_booking(context.settings.database_url, raw_session, booking_id, submission.forfeit_funding, idempotency_key, context.now())
    if result is None: raise HTTPException(status_code=409)
    return result


@router.get("/api/student/bookings/{booking_id}/calendar.ics")
async def calendar_export(booking_id: str, request: Request):
    raw_session = require_session(request, "student")
    exported = booking_calendar_export(context_from(request).settings.database_url, raw_session, booking_id)
    if exported is None: raise HTTPException(status_code=404)
    filename, body = exported
    return Response(content=body, media_type="text/calendar", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
