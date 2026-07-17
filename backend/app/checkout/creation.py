from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.availability import derive_bookable_slots
from app.bookings.shared import account_id
from app.checkout.provider import create_provider_checkout


def response(row) -> dict:
    return {"checkout_session_id": row["provider_session_id"], "checkout_url": row["checkout_url"],
            "amount_cents": row["amount_cents"], "currency": row["currency"], "status": row["status"]}


def start_checkout(database_url: str, raw_session: str, start: datetime, focus: str | None, key: str, now: datetime,
                   provider_mode: str = "fake", provider_secret: str = "", origin: str = "") -> dict | None:
    _, slots = derive_bookable_slots(database_url, now)
    valid_slot = any(slot["start_at"] == start for slot in slots)
    engine, connection = create_engine(database_url), None
    try:
        connection = engine.connect(); connection.exec_driver_sql("BEGIN IMMEDIATE")
        student = account_id(connection, raw_session)
        if student is None: connection.rollback(); return None
        existing = connection.execute(text("SELECT * FROM checkout_sessions WHERE idempotency_key = :key AND student_account_id = :student"), {"key": key, "student": student}).mappings().first()
        if existing is not None: connection.commit(); return response(existing)
        if not valid_slot: connection.rollback(); return None
        funding = connection.execute(text(
            "SELECT COALESCE(SUM(CASE WHEN event_type LIKE 'promotion_%' THEN quantity ELSE 0 END), 0), "
            "COALESCE(SUM(CASE WHEN event_type LIKE 'credit_%' THEN quantity ELSE 0 END), 0) "
            "FROM credit_ledger_entries WHERE student_account_id = :student"
        ), {"student": student}).one()
        if funding[0] > 0 or funding[1] > 0: connection.rollback(); return None
        end = start + timedelta(hours=1)
        conflict = connection.execute(text(
            "SELECT 1 FROM bookings WHERE status = 'upcoming' AND start_at < :end AND end_at > :start "
            "UNION ALL SELECT 1 FROM blocked_times WHERE start_at < :end AND end_at > :start "
            "UNION ALL SELECT 1 FROM slot_holds WHERE expires_at > :now AND start_at < :end AND end_at > :start LIMIT 1"
        ), {"start": start, "end": end, "now": now}).first()
        if conflict is not None: connection.rollback(); return None
        settings = connection.execute(text(
            "SELECT currency, session_price_cents, tutor_timezone, default_meeting_details FROM tutor_settings WHERE id = 1"
        )).mappings().one()
        provider_id, checkout_url = create_provider_checkout(
            provider_mode, provider_secret, origin, settings["session_price_cents"], settings["currency"], student,
            start.isoformat().replace("+00:00", "Z"),
        )
        hold_id, checkout_id = str(uuid4()), str(uuid4())
        expires = now + timedelta(minutes=30)
        connection.execute(text(
            "INSERT INTO slot_holds (id, student_account_id, start_at, end_at, expires_at) VALUES (:id, :student, :start, :end, :expires)"
        ), {"id": hold_id, "student": student, "start": start, "end": end, "expires": expires})
        connection.execute(text(
            "INSERT INTO checkout_sessions (id, provider_session_id, checkout_url, student_account_id, slot_hold_id, start_at, end_at, "
            "amount_cents, currency, focus, meeting_details_snapshot, tutor_timezone_snapshot, status, idempotency_key, expires_at, created_at) "
            "VALUES (:id, :provider, :url, :student, :hold, :start, :end, :amount, :currency, :focus, :details, :timezone, 'pending', :key, :expires, :now)"
        ), {"id": checkout_id, "provider": provider_id, "url": checkout_url, "student": student, "hold": hold_id, "start": start, "end": end,
            "amount": settings["session_price_cents"], "currency": settings["currency"], "focus": focus,
            "details": settings["default_meeting_details"], "timezone": settings["tutor_timezone"], "key": key, "expires": expires, "now": now})
        connection.commit()
        return {"checkout_session_id": provider_id, "checkout_url": checkout_url, "amount_cents": settings["session_price_cents"], "currency": settings["currency"], "status": "pending"}
    except Exception:
        if connection is not None: connection.rollback()
        raise
    finally:
        if connection is not None: connection.close()
        engine.dispose()
