from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.bookings.shared import account_id, booking_values, insert_booking, no_conflict, response, settings_snapshot, valid_slot


def create_student_booking(database_url: str, raw_session: str, start: datetime, focus: str | None, key: str, now: datetime) -> dict | None:
    engine = create_engine(database_url)
    connection = engine.connect()
    try:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        student_id = account_id(connection, raw_session)
        if student_id is None:
            connection.rollback()
            return None
        existing = connection.execute(text(
            "SELECT bookings.*, tutor_timezone FROM bookings, tutor_settings "
            "WHERE idempotency_key = :key AND student_account_id = :student AND tutor_settings.id = 1"
        ), {"key": key, "student": student_id}).mappings().first()
        if existing is not None:
            connection.commit()
            values = {"id": existing["id"], "start": existing["start_at"], "end": existing["end_at"],
                      "funding": existing["funding_kind"], "focus": existing["focus"],
                      "details": existing["meeting_details_snapshot"], "price": existing["price_cents_snapshot"],
                      "currency": existing["currency_snapshot"]}
            return response(values, existing, existing["status"])
        if not valid_slot(database_url, start, now):
            connection.rollback()
            return None
        end = start + timedelta(hours=1)
        if not no_conflict(connection, student_id, start, end, now):
            connection.rollback()
            return None
        promotion = connection.execute(text(
            "SELECT COALESCE(SUM(quantity), 0) FROM credit_ledger_entries WHERE student_account_id = :student "
            "AND event_type LIKE 'promotion_%'"
        ), {"student": student_id}).scalar_one()
        credits = connection.execute(text(
            "SELECT COALESCE(SUM(quantity), 0) FROM credit_ledger_entries WHERE student_account_id = :student "
            "AND event_type LIKE 'credit_%'"
        ), {"student": student_id}).scalar_one()
        funding = "first_session_promotion" if promotion > 0 else "session_credit" if credits > 0 else None
        if funding is None:
            connection.rollback()
            return None
        settings = settings_snapshot(connection)
        values = booking_values(student_id, start, focus, funding, key, now, settings)
        insert_booking(connection, values)
        event_type = "promotion_consumed" if funding == "first_session_promotion" else "credit_booking_redemption"
        connection.execute(text(
            "INSERT INTO credit_ledger_entries (id, student_account_id, event_type, quantity, reason, idempotency_key, created_at) "
            "VALUES (:id, :student, :event, -1, 'Booking funding', :key, :now)"
        ), {"id": str(uuid4()), "student": student_id, "event": event_type, "key": f"booking:{values['id']}", "now": now})
        connection.commit()
        return response(values, settings)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
        engine.dispose()
