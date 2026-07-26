import json

from fastapi import APIRouter, Header, Request
from starlette.exceptions import HTTPException

from app.checkout import checkout_status, fulfill_event, start_checkout
from app.checkout.provider import valid_webhook_signature
from app.http import context_from, require_mutation, require_session
from app.models import CheckoutInput, CheckoutResponse, RefundRequestResponse, StudentRefundList, TutorRefundList
from app.refunds import approve_refund, create_refund_request, decline_refund, list_student_refunds, list_tutor_refunds
from app.refunds.provider import refund_payment

router = APIRouter()


@router.post("/api/student/checkouts", status_code=201, response_model=CheckoutResponse)
async def create_checkout(submission: CheckoutInput, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    raw_session = require_mutation(request, "student")
    context = context_from(request)
    result = start_checkout(
        context.settings.database_url, raw_session, submission.start_at, submission.focus, idempotency_key, context.now(),
        context.settings.stripe_provider_mode, context.settings.stripe_secret_key.get_secret_value(),
        context.settings.application_origin,
    )
    if result is None: raise HTTPException(status_code=409)
    return result


@router.get("/api/student/checkouts/{provider_id}", response_model=CheckoutResponse)
async def view_checkout(provider_id: str, request: Request):
    raw_session = require_session(request, "student")
    context = context_from(request)
    result = checkout_status(context.settings.database_url, raw_session, provider_id, context.now())
    if result is None: raise HTTPException(status_code=404)
    return result


@router.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    context = context_from(request)
    body = await request.body()
    supplied = request.headers.get("stripe-signature", "")
    secret = context.settings.stripe_webhook_secret.get_secret_value()
    if not valid_webhook_signature(body, supplied, secret, context.now()):
        raise HTTPException(status_code=400)
    try: event = json.loads(body)
    except json.JSONDecodeError: raise HTTPException(status_code=400) from None
    outcome = fulfill_event(context.settings.database_url, event, context.now())
    if outcome == "mismatch": raise HTTPException(status_code=409)
    return {"status": outcome}


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
    settings = context.settings
    outcome, result = approve_refund(
        settings.database_url,
        request_id,
        lambda payment, amount, currency, key: refund_payment(
            settings.stripe_provider_mode,
            settings.stripe_secret_key.get_secret_value(),
            payment,
            amount,
            currency,
            key,
        ),
        context.now(),
    )
    if outcome == "provider_failure": raise HTTPException(status_code=502)
    if result is None: raise HTTPException(status_code=409)
    return result
