from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.availability import derive_bookable_slots
from app.bookings.tutor_operations import booking_response


def aware(value) -> datetime:
    if isinstance(value, str): value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


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
    _, slots = derive_bookable_slots(database_url, now)
    valid_target = any(slot["start_at"] == start for slot in slots)
    engine, connection = create_engine(database_url), None
    try:
        connection = engine.connect(); connection.exec_driver_sql("BEGIN IMMEDIATE")
        booking = owned_booking(connection, booking_id, raw_session)
        if booking is None: connection.rollback(); return None
        if receipt_exists(connection, booking_id, key, "reschedule"):
            connection.commit(); return booking_response(booking)
        if not valid_target: connection.rollback(); return None
        if booking["status"] != "upcoming" or aware(booking["start_at"]) - now < timedelta(hours=24):
            connection.rollback(); return None
        end = start + timedelta(hours=1)
        conflict = connection.execute(text(
            "SELECT 1 FROM bookings WHERE id != :id AND status = 'upcoming' AND start_at < :end AND end_at > :start "
            "UNION ALL SELECT 1 FROM blocked_times WHERE start_at < :end AND end_at > :start "
            "UNION ALL SELECT 1 FROM slot_holds WHERE expires_at > :now AND start_at < :end AND end_at > :start LIMIT 1"
        ), {"id": booking_id, "start": start, "end": end, "now": now}).first()
        if conflict is not None: connection.rollback(); return None
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
