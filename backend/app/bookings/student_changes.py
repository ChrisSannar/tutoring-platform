from datetime import datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.bookings.shared import no_conflict, valid_slot
from app.bookings.tutor_operations import booking_response
from app.occupancy import utc_aware


def owned_booking(connection, booking_id: str, raw_session: str):
    return connection.execute(text(
        "SELECT bookings.*, tutor_timezone FROM bookings JOIN authentication_sessions ON "
        "authentication_sessions.account_id = bookings.student_account_id JOIN tutor_settings ON "
        "tutor_settings.id = 1 WHERE bookings.id = :id AND session_hash = :hash"
    ), {"id": booking_id, "hash": sha256(raw_session.encode()).hexdigest()}).mappings().first()


def receipt_exists(connection, booking_id: str, key: str, kind: str) -> bool:
    return connection.execute(text(
        "SELECT 1 FROM booking_change_receipts WHERE booking_id = :booking AND idempotency_key = :key AND kind = :kind"
    ), {"booking": booking_id, "key": key, "kind": kind}).first() is not None


def add_receipt(connection, booking_id: str, key: str, kind: str, now: datetime) -> None:
    connection.execute(text(
        "INSERT INTO booking_change_receipts (id, booking_id, kind, idempotency_key, created_at) "
        "VALUES (:id, :booking, :kind, :key, :now)"
    ), {"id": str(uuid4()), "booking": booking_id, "kind": kind, "key": key, "now": now})


def reschedule_student_booking(database_url: str, raw_session: str, booking_id: str, start: datetime, key: str, now: datetime) -> dict | None:
    start = utc_aware(start)
    engine, connection = create_engine(database_url), None
    try:
        connection = engine.connect(); connection.exec_driver_sql("BEGIN IMMEDIATE")
        valid_target = valid_slot(
            connection,
            database_url,
            start,
            now,
            exclude_booking_id=booking_id,
        )
        booking = owned_booking(connection, booking_id, raw_session)
        if booking is None: connection.rollback(); return None
        if receipt_exists(connection, booking_id, key, "reschedule"):
            connection.commit(); return booking_response(booking)
        if not valid_target: connection.rollback(); return None
        if booking["status"] != "upcoming" or utc_aware(booking["start_at"]) - utc_aware(now) < timedelta(hours=24):
            connection.rollback(); return None
        end = start + timedelta(hours=1)
        if not no_conflict(
            connection,
            booking["student_account_id"],
            start,
            end,
            now,
            exclude_booking_id=booking_id,
        ):
            connection.rollback(); return None
        connection.execute(text("UPDATE bookings SET start_at = :start, end_at = :end WHERE id = :id"), {"id": booking_id, "start": start, "end": end})
        add_receipt(connection, booking_id, key, "reschedule", now)
        connection.commit()
        return booking_response({**dict(booking), "start_at": start, "end_at": end})
    except Exception:
        if connection is not None: connection.rollback()
        raise
    finally:
        if connection is not None: connection.close()
        engine.dispose()
