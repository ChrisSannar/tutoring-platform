from datetime import datetime, timedelta

from sqlalchemy import create_engine, text

from app.bookings.shared import booking_values, insert_booking, no_conflict, response, settings_snapshot, valid_slot
from app.occupancy import utc_aware


def create_complimentary_booking(database_url: str, student_id: str, start: datetime, focus: str | None, key: str, now: datetime, override_id: str | None, warning_acknowledged: bool) -> dict | None:
    start = utc_aware(start)
    engine = create_engine(database_url)
    connection = engine.connect()
    try:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        normal_slot = valid_slot(connection, database_url, start, now)
        existing = connection.execute(text(
            "SELECT bookings.*, tutor_timezone FROM bookings, tutor_settings WHERE idempotency_key = :key AND tutor_settings.id = 1"
        ), {"key": key}).mappings().first()
        if existing is not None:
            connection.commit()
            values = {"id": existing["id"], "start": existing["start_at"], "end": existing["end_at"], "funding": existing["funding_kind"], "focus": existing["focus"], "details": existing["meeting_details_snapshot"], "price": existing["price_cents_snapshot"], "currency": existing["currency_snapshot"]}
            return response(values, existing, existing["status"])
        override = None if override_id is None else connection.execute(text(
            "SELECT 1 FROM tutor_overrides WHERE id = :id AND start_at = :start"
        ), {"id": override_id, "start": start}).first()
        allowed = normal_slot or (override is not None and warning_acknowledged)
        student_exists = connection.execute(text(
            "SELECT 1 FROM accounts WHERE id = :id AND role = 'student'"
        ), {"id": student_id}).first()
        end = start + timedelta(hours=1)
        if not allowed or student_exists is None or not no_conflict(connection, student_id, start, end, now):
            connection.rollback()
            return None
        settings = settings_snapshot(connection)
        values = booking_values(student_id, start, focus, "complimentary", key, now, settings)
        insert_booking(connection, values)
        connection.commit()
        return response(values, settings)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
        engine.dispose()
