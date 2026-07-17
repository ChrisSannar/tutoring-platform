from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.bookings.student_changes import add_receipt, aware, owned_booking, receipt_exists
from app.bookings.tutor_operations import booking_response


def restoration_event(funding_kind: str) -> str | None:
    return {"first_session_promotion": "promotion_restored", "session_credit": "credit_booking_restoration", "paid": "credit_paid_cancellation"}.get(funding_kind)


def cancel_student_booking(database_url: str, raw_session: str, booking_id: str, forfeit: bool, key: str, now: datetime) -> dict | None:
    engine, connection = create_engine(database_url), None
    try:
        connection = engine.connect(); connection.exec_driver_sql("BEGIN IMMEDIATE")
        booking = owned_booking(connection, booking_id, raw_session)
        if booking is None: connection.rollback(); return None
        if receipt_exists(connection, booking_id, key, "cancel"):
            connection.commit(); return booking_response(booking)
        if booking["status"] != "upcoming": connection.rollback(); return None
        late = aware(booking["start_at"]) - now < timedelta(hours=24)
        if late and not forfeit: connection.rollback(); return None
        event = None if late else restoration_event(booking["funding_kind"])
        if event is not None:
            connection.execute(text(
                "INSERT INTO credit_ledger_entries (id, student_account_id, event_type, quantity, reason, idempotency_key, created_at) "
                "VALUES (:id, :student, :event, 1, 'Booking cancellation restoration', :key, :now)"
            ), {"id": str(uuid4()), "student": booking["student_account_id"], "event": event, "key": f"cancel:{booking_id}", "now": now})
        connection.execute(text("UPDATE bookings SET status = 'cancelled' WHERE id = :id"), {"id": booking_id})
        add_receipt(connection, booking_id, key, "cancel", now)
        connection.commit()
        return booking_response({**dict(booking), "status": "cancelled"})
    except Exception:
        if connection is not None: connection.rollback()
        raise
    finally:
        if connection is not None: connection.close()
        engine.dispose()
