from datetime import datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import text

from app.availability import derive_bookable_slots
from app.occupancy import interval_is_free, utc_aware


def account_id(connection, raw_session: str) -> str | None:
    return connection.execute(text(
        "SELECT account_id FROM authentication_sessions JOIN accounts ON accounts.id = account_id "
        "WHERE session_hash = :hash AND revoked_at IS NULL AND accounts.role = 'student'"
    ), {"hash": sha256(raw_session.encode()).hexdigest()}).scalar()


def valid_slot(
    connection,
    database_url: str,
    start: datetime,
    now: datetime,
    *,
    exclude_booking_id: str | None = None,
) -> bool:
    _, slots = derive_bookable_slots(
        database_url,
        now,
        connection=connection,
        exclude_booking_id=exclude_booking_id,
    )
    start_at = utc_aware(start)
    return any(slot["start_at"] == start_at for slot in slots)


def no_conflict(
    connection,
    student_id: str | None,
    start: datetime,
    end: datetime,
    now: datetime,
    *,
    exclude_booking_id: str | None = None,
) -> bool:
    upcoming = None
    if student_id is not None:
        upcoming = connection.execute(text(
            "SELECT 1 FROM bookings WHERE student_account_id = :student "
            "AND status = 'upcoming' AND (:booking IS NULL OR id != :booking)"
        ), {"student": student_id, "booking": exclude_booking_id}).first()
    return interval_is_free(
        connection,
        start,
        end,
        now,
        exclude_booking_id=exclude_booking_id,
    ) and upcoming is None


def settings_snapshot(connection) -> dict:
    return dict(connection.execute(text(
        "SELECT currency, session_price_cents, tutor_timezone, default_meeting_details "
        "FROM tutor_settings WHERE id = 1"
    )).mappings().one())


def booking_values(student_id: str, start: datetime, focus: str | None, funding: str, key: str, now: datetime, settings: dict) -> dict:
    return {
        "id": str(uuid4()), "student": student_id, "start": start,
        "end": start + timedelta(hours=1), "focus": focus, "funding": funding,
        "details": settings["default_meeting_details"], "price": settings["session_price_cents"],
        "currency": settings["currency"], "key": key, "now": now,
    }


def insert_booking(connection, values: dict) -> None:
    connection.execute(text(
        "INSERT INTO bookings (id, student_account_id, start_at, end_at, status, funding_kind, focus, "
        "meeting_details_snapshot, price_cents_snapshot, currency_snapshot, idempotency_key, created_at) "
        "VALUES (:id, :student, :start, :end, 'upcoming', :funding, :focus, :details, :price, :currency, :key, :now)"
    ), values)


def response(values: dict, settings: dict, status: str = "upcoming") -> dict:
    return {"id": values["id"], "start_at": values["start"], "end_at": values["end"], "duration_minutes": 60,
            "tutor_timezone": settings["tutor_timezone"], "funding_kind": values["funding"], "focus": values["focus"],
            "meeting_details": values["details"], "price_cents": values["price"], "currency": values["currency"], "status": status}
