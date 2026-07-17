from fastapi import APIRouter, Header, Request
from starlette.exceptions import HTTPException

from app.http.context import context_from
from app.http.security import require_mutation, require_session
from app.models.refunds import RefundRequestResponse, StudentRefundList, TutorRefundList
from app.refunds import approve_refund, create_refund_request, decline_refund, list_student_refunds, list_tutor_refunds

router = APIRouter()


@router.post("/api/student/bookings/{booking_id}/refund-request", status_code=201, response_model=RefundRequestResponse)
async def request_refund(booking_id: str, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    raw_session = require_mutation(request, "student")
    context = context_from(request)
    result = create_refund_request(context.settings.database_url, raw_session, booking_id, idempotency_key, context.now())
    if result is None: raise HTTPException(status_code=404)
    return result


@router.get("/api/student/refund-requests", response_model=StudentRefundList)
async def student_refunds(request: Request):
    raw_session = require_session(request, "student")
    return {"refund_requests": list_student_refunds(context_from(request).settings.database_url, raw_session)}


@router.get("/api/tutor/refund-requests", response_model=TutorRefundList)
async def tutor_refunds(request: Request):
    require_session(request, "tutor")
    return {"refund_requests": list_tutor_refunds(context_from(request).settings.database_url)}


@router.post("/api/tutor/refund-requests/{request_id}/decline", response_model=RefundRequestResponse)
async def decline(request_id: str, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    require_mutation(request, "tutor")
    context = context_from(request)
    result = decline_refund(context.settings.database_url, request_id, context.now())
    if result is None: raise HTTPException(status_code=409)
    return result


@router.post("/api/tutor/refund-requests/{request_id}/approve", response_model=RefundRequestResponse)
async def approve(request_id: str, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    require_mutation(request, "tutor")
    context = context_from(request)
    outcome, result = approve_refund(context.settings.database_url, request_id, context.refund_payment, context.now())
    if outcome == "provider_failure": raise HTTPException(status_code=502)
    if result is None: raise HTTPException(status_code=409)
    return result
