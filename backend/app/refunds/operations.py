from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.bookings.shared import account_id
from app.refunds.queries import response


def create_refund_request(database_url: str, raw_session: str, booking_id: str, key: str, now: datetime) -> dict | None:
    engine, connection = create_engine(database_url), None
    try:
        connection = engine.connect(); connection.exec_driver_sql("BEGIN IMMEDIATE")
        student = account_id(connection, raw_session)
        row = connection.execute(text("SELECT * FROM refund_requests WHERE booking_id = :booking"), {"booking": booking_id}).mappings().first()
        if row is not None:
            if row["student_account_id"] != student: connection.rollback(); return None
            connection.commit(); return response(row)
        eligible = connection.execute(text(
            "SELECT bookings.student_account_id, payment_evidence.id AS evidence_id, payment_evidence.amount_cents, "
            "payment_evidence.currency FROM bookings JOIN payment_evidence ON payment_evidence.booking_id = bookings.id "
            "WHERE bookings.id = :booking AND bookings.student_account_id = :student AND bookings.status = 'cancelled' "
            "AND bookings.funding_kind = 'paid' AND EXISTS (SELECT 1 FROM credit_ledger_entries WHERE "
            "student_account_id = :student AND event_type = 'credit_paid_cancellation' AND idempotency_key = :cancel_key)"
        ), {"booking": booking_id, "student": student, "cancel_key": f"cancel:{booking_id}"}).mappings().first()
        balance = connection.execute(text(
            "SELECT COALESCE(SUM(quantity), 0) FROM credit_ledger_entries WHERE student_account_id = :student "
            "AND event_type LIKE 'credit_%'"
        ), {"student": student}).scalar_one()
        if eligible is None or balance < 1: connection.rollback(); return None
        request_id = str(uuid4())
        connection.execute(text(
            "INSERT INTO refund_requests (id, booking_id, student_account_id, payment_evidence_id, amount_cents, "
            "currency, status, idempotency_key, created_at) VALUES (:id, :booking, :student, :evidence, :amount, "
            ":currency, 'pending', :key, :now)"
        ), {"id": request_id, "booking": booking_id, "student": student, "evidence": eligible["evidence_id"],
            "amount": eligible["amount_cents"], "currency": eligible["currency"], "key": key, "now": now})
        connection.execute(text(
            "INSERT INTO credit_ledger_entries (id, student_account_id, event_type, quantity, reason, idempotency_key, "
            "created_at) VALUES (:id, :student, 'credit_refund_freeze', -1, 'Refund Request pending review', :key, :now)"
        ), {"id": str(uuid4()), "student": student, "key": f"refund-freeze:{booking_id}", "now": now})
        connection.commit()
        return {"id": request_id, "booking_id": booking_id, "amount_cents": eligible["amount_cents"],
                "currency": eligible["currency"], "status": "pending", "created_at": now}
    except Exception:
        if connection is not None: connection.rollback()
        raise
    finally:
        if connection is not None: connection.close()
        engine.dispose()


def decline_refund(database_url: str, request_id: str, now: datetime) -> dict | None:
    engine, connection = create_engine(database_url), None
    try:
        connection = engine.connect(); connection.exec_driver_sql("BEGIN IMMEDIATE")
        row = connection.execute(text("SELECT * FROM refund_requests WHERE id = :id"), {"id": request_id}).mappings().first()
        if row is None: connection.rollback(); return None
        if row["status"] == "declined": connection.commit(); return response(row)
        if row["status"] != "pending": connection.rollback(); return None
        connection.execute(text(
            "INSERT INTO credit_ledger_entries (id, student_account_id, event_type, quantity, reason, idempotency_key, "
            "created_at) VALUES (:entry, :student, 'credit_refund_unfreeze', 1, 'Refund Request declined', :key, :now)"
        ), {"entry": str(uuid4()), "student": row["student_account_id"], "key": f"refund-unfreeze:{request_id}", "now": now})
        connection.execute(text("UPDATE refund_requests SET status = 'declined', reviewed_at = :now WHERE id = :id"), {"now": now, "id": request_id})
        connection.commit(); return response({**dict(row), "status": "declined"})
    finally:
        if connection is not None: connection.close()
        engine.dispose()


def approve_refund(database_url: str, request_id: str, provider, now: datetime) -> tuple[str, dict | None]:
    engine, connection = create_engine(database_url), None
    try:
        connection = engine.connect(); connection.exec_driver_sql("BEGIN IMMEDIATE")
        row = connection.execute(text(
            "SELECT refund_requests.*, payment_evidence.provider_payment_id FROM refund_requests JOIN payment_evidence "
            "ON payment_evidence.id = payment_evidence_id WHERE refund_requests.id = :id"
        ), {"id": request_id}).mappings().first()
        if row is None: connection.rollback(); return "conflict", None
        if row["status"] == "refunded": connection.commit(); return "ok", response(row)
        if row["status"] != "pending": connection.rollback(); return "conflict", None
        succeeded, provider_id = provider(row["provider_payment_id"], row["amount_cents"], row["currency"], request_id)
        if not succeeded or not provider_id: connection.rollback(); return "provider_failure", None
        connection.execute(text(
            "INSERT INTO refund_evidence (id, refund_request_id, provider_refund_id, amount_cents, currency, created_at) "
            "VALUES (:id, :request, :provider, :amount, :currency, :now)"
        ), {"id": str(uuid4()), "request": request_id, "provider": provider_id, "amount": row["amount_cents"],
            "currency": row["currency"], "now": now})
        connection.execute(text("UPDATE refund_requests SET status = 'refunded', reviewed_at = :now WHERE id = :id"), {"now": now, "id": request_id})
        connection.commit(); return "ok", response({**dict(row), "status": "refunded"})
    finally:
        if connection is not None: connection.close()
        engine.dispose()
