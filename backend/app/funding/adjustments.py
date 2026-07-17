from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.funding.errors import CreditAdjustmentConflict


def adjust_session_credits(
    database_url: str,
    student_id: str,
    quantity: int,
    reason: str,
    idempotency_key: str,
) -> dict[str, int]:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            existing = connection.execute(
                text(
                    "SELECT student_account_id, quantity, reason FROM "
                    "credit_ledger_entries WHERE idempotency_key = :key"
                ),
                {"key": idempotency_key},
            ).mappings().first()
            balance = connection.execute(
                text(
                    "SELECT COALESCE(SUM(quantity), 0) FROM credit_ledger_entries "
                    "WHERE student_account_id = :student AND event_type LIKE 'credit_%'"
                ),
                {"student": student_id},
            ).scalar_one()
            if existing is not None:
                if dict(existing) != {
                    "student_account_id": student_id,
                    "quantity": quantity,
                    "reason": reason,
                }:
                    raise CreditAdjustmentConflict
                return {"session_credits": balance}
            student_exists = connection.execute(
                text(
                    "SELECT 1 FROM accounts WHERE id = :id AND role = 'student'"
                ),
                {"id": student_id},
            ).first()
            if student_exists is None or balance + quantity < 0:
                raise CreditAdjustmentConflict
            connection.execute(
                text(
                    "INSERT INTO credit_ledger_entries (id, student_account_id, "
                    "event_type, quantity, reason, idempotency_key, created_at) VALUES "
                    "(:id, :student, 'credit_adjustment', :quantity, :reason, :key, :now)"
                ),
                {
                    "id": str(uuid4()),
                    "student": student_id,
                    "quantity": quantity,
                    "reason": reason,
                    "key": idempotency_key,
                    "now": datetime.now(timezone.utc),
                },
            )
            return {"session_credits": balance + quantity}
    finally:
        engine.dispose()
