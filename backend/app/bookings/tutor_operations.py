from datetime import datetime, timedelta

from sqlalchemy import create_engine, text

from app.bookings.shared import no_conflict, valid_slot
from app.occupancy import utc_aware


def booking_response(row) -> dict:
    return {"id": row["id"], "start_at": row["start_at"], "end_at": row["end_at"], "duration_minutes": 60,
            "tutor_timezone": row["tutor_timezone"], "funding_kind": row["funding_kind"], "focus": row["focus"],
            "meeting_details": row["meeting_details_snapshot"], "price_cents": row["price_cents_snapshot"],
            "currency": row["currency_snapshot"], "status": row["status"]}


def update_meeting_details(database_url: str, booking_id: str, details: str | None) -> dict | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            row = connection.execute(text(
                "UPDATE bookings SET meeting_details_snapshot = :details WHERE id = :id RETURNING *"
            ), {"id": booking_id, "details": details}).mappings().first()
            if row is None: return None
            settings = connection.execute(text("SELECT tutor_timezone FROM tutor_settings WHERE id = 1")).mappings().one()
            return booking_response({**dict(row), **dict(settings)})
    finally:
        engine.dispose()


def move_booking(database_url: str, booking_id: str, start: datetime, now: datetime, override_id: str | None, acknowledged: bool) -> dict | None:
    start = utc_aware(start)
    engine = create_engine(database_url)
    connection = engine.connect()
    try:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        normal = valid_slot(
            connection,
            database_url,
            start,
            now,
            exclude_booking_id=booking_id,
        )
        booking = connection.execute(text("SELECT 1 FROM bookings WHERE id = :id AND status = 'upcoming'"), {"id": booking_id}).first()
        override = None if override_id is None else connection.execute(text(
            "SELECT 1 FROM tutor_overrides WHERE id = :id AND start_at = :start"
        ), {"id": override_id, "start": start}).first()
        end = start + timedelta(hours=1)
        free = no_conflict(
            connection,
            None,
            start,
            end,
            now,
            exclude_booking_id=booking_id,
        )
        if booking is None or not free or not (normal or (override is not None and acknowledged)):
            connection.rollback()
            return None
        row = connection.execute(text(
            "UPDATE bookings SET start_at = :start, end_at = :end WHERE id = :id RETURNING *"
        ), {"id": booking_id, "start": start, "end": end}).mappings().one()
        timezone_name = connection.execute(text("SELECT tutor_timezone FROM tutor_settings WHERE id = 1")).scalar_one()
        connection.commit()
        return booking_response({**dict(row), "tutor_timezone": timezone_name})
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
        engine.dispose()
