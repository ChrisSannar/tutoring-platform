from fastapi import APIRouter, Header, Request
from starlette.exceptions import HTTPException

from app.funding import CreditAdjustmentConflict, adjust_session_credits, list_credit_ledger
from app.http.context import context_from
from app.http.security import require_mutation, require_session
from app.models.funding import (
    CreditAdjustmentRequest,
    CreditBalanceResponse,
    CreditLedgerResponse,
)

router = APIRouter()


@router.post(
    "/api/tutor/students/{student_id}/credits",
    response_model=CreditBalanceResponse,
)
async def adjust_student_credits(
    student_id: str,
    adjustment: CreditAdjustmentRequest,
    request: Request,
    idempotency_key: str = Header(),
) -> CreditBalanceResponse:
    require_mutation(request, "tutor")
    try:
        balance = adjust_session_credits(
            context_from(request).settings.database_url,
            student_id,
            adjustment.quantity,
            adjustment.reason,
            idempotency_key,
        )
    except CreditAdjustmentConflict:
        raise HTTPException(status_code=409) from None
    return CreditBalanceResponse.model_validate(balance)


@router.get(
    "/api/tutor/students/{student_id}/credit-ledger",
    response_model=CreditLedgerResponse,
)
async def view_student_credit_ledger(
    student_id: str, request: Request
) -> CreditLedgerResponse:
    require_session(request, "tutor")
    events = list_credit_ledger(
        context_from(request).settings.database_url, student_id
    )
    if events is None:
        raise HTTPException(status_code=404)
    return CreditLedgerResponse.model_validate({"events": events})
