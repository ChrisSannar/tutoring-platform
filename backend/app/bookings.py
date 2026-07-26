from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.availability import derive_bookable_slots
from app.database import db_connection
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


def booking_response(row) -> dict:
    return {"id": row["id"], "start_at": row["start_at"], "end_at": row["end_at"], "duration_minutes": 60,
            "tutor_timezone": row["tutor_timezone"], "funding_kind": row["funding_kind"], "focus": row["focus"],
            "meeting_details": row["meeting_details_snapshot"], "price_cents": row["price_cents_snapshot"],
            "currency": row["currency_snapshot"], "status": row["status"]}


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


def update_meeting_details(database_url: str, booking_id: str, details: str | None) -> dict | None:
    with db_connection(database_url) as connection:
        row = connection.execute(text(
            "UPDATE bookings SET meeting_details_snapshot = :details WHERE id = :id RETURNING *"
        ), {"id": booking_id, "details": details}).mappings().first()
        if row is None: return None
        settings = connection.execute(text("SELECT tutor_timezone FROM tutor_settings WHERE id = 1")).mappings().one()
        return booking_response({**dict(row), **dict(settings)})


def move_booking(database_url: str, booking_id: str, start: datetime, now: datetime, override_id: str | None, acknowledged: bool) -> dict | None:
    start = utc_aware(start)
    with db_connection(database_url, mode="immediate") as connection:
        try:
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


def reschedule_student_booking(database_url: str, raw_session: str, booking_id: str, start: datetime, key: str, now: datetime) -> dict | None:
    start = utc_aware(start)
    with db_connection(database_url, mode="immediate") as connection:
        try:
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
            connection.rollback()
            raise


def create_student_booking(database_url: str, raw_session: str, start: datetime, focus: str | None, key: str, now: datetime) -> dict | None:
    start = utc_aware(start)
    with db_connection(database_url, mode="immediate") as connection:
        try:
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
            if not valid_slot(connection, database_url, start, now):
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


def create_complimentary_booking(database_url: str, student_id: str, start: datetime, focus: str | None, key: str, now: datetime, override_id: str | None, warning_acknowledged: bool) -> dict | None:
    start = utc_aware(start)
    with db_connection(database_url, mode="immediate") as connection:
        try:
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


def restoration_event(funding_kind: str) -> str | None:
    return {"first_session_promotion": "promotion_restored", "session_credit": "credit_booking_restoration", "paid": "credit_paid_cancellation"}.get(funding_kind)


def cancel_student_booking(database_url: str, raw_session: str, booking_id: str, forfeit: bool, key: str, now: datetime) -> dict | None:
    with db_connection(database_url, mode="immediate") as connection:
        try:
            booking = owned_booking(connection, booking_id, raw_session)
            if booking is None: connection.rollback(); return None
            if receipt_exists(connection, booking_id, key, "cancel"):
                connection.commit(); return booking_response(booking)
            if booking["status"] != "upcoming": connection.rollback(); return None
            late = utc_aware(booking["start_at"]) - utc_aware(now) < timedelta(hours=24)
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
            connection.rollback()
            raise


def upcoming_booking(database_url: str, raw_session: str) -> dict | None:
    with db_connection(database_url, mode="read") as connection:
        row = connection.execute(text(
            "SELECT bookings.id, start_at, end_at, funding_kind, focus, meeting_details_snapshot, "
            "price_cents_snapshot, currency_snapshot, status, tutor_timezone FROM bookings "
            "JOIN authentication_sessions ON authentication_sessions.account_id = bookings.student_account_id "
            "JOIN tutor_settings ON tutor_settings.id = 1 WHERE session_hash = :hash AND status = 'upcoming'"
        ), {"hash": sha256(raw_session.encode()).hexdigest()}).mappings().first()
        if row is None: return None
        return {"id": row["id"], "start_at": row["start_at"], "end_at": row["end_at"], "duration_minutes": 60,
                "tutor_timezone": row["tutor_timezone"], "funding_kind": row["funding_kind"], "focus": row["focus"],
                "meeting_details": row["meeting_details_snapshot"], "price_cents": row["price_cents_snapshot"],
                "currency": row["currency_snapshot"], "status": row["status"]}


def tutor_calendar(database_url: str) -> list[dict]:
    with db_connection(database_url, mode="read") as connection:
        rows = connection.execute(text(
            "SELECT bookings.id, start_at, end_at, funding_kind, focus, meeting_details_snapshot, "
            "price_cents_snapshot, currency_snapshot, status, tutor_timezone, accounts.id AS student_id, "
            "accounts.display_name, accounts.email FROM bookings JOIN accounts ON accounts.id = "
            "student_account_id JOIN tutor_settings ON tutor_settings.id = 1 ORDER BY start_at"
        )).mappings()
        return [{"id": row["id"], "start_at": row["start_at"], "end_at": row["end_at"],
                 "duration_minutes": 60, "tutor_timezone": row["tutor_timezone"],
                 "funding_kind": row["funding_kind"], "focus": row["focus"],
                 "meeting_details": row["meeting_details_snapshot"], "price_cents": row["price_cents_snapshot"],
                 "currency": row["currency_snapshot"], "status": row["status"],
                 "student": {"id": row["student_id"], "display_name": row["display_name"], "email": row["email"]}}
                for row in rows]


def escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def booking_calendar_export(database_url: str, raw_session: str, booking_id: str) -> tuple[str, str] | None:
    with db_connection(database_url, mode="read") as connection:
        row = connection.execute(text(
            "SELECT bookings.*, tutor_timezone FROM bookings JOIN authentication_sessions ON "
            "authentication_sessions.account_id = student_account_id JOIN tutor_settings ON tutor_settings.id = 1 "
            "WHERE bookings.id = :id AND session_hash = :hash AND status = 'upcoming'"
        ), {"id": booking_id, "hash": sha256(raw_session.encode()).hexdigest()}).mappings().first()
        if row is None: return None
        start, end = row["start_at"], row["end_at"]
        if isinstance(start, str): start = __import__("datetime").datetime.fromisoformat(start)
        if isinstance(end, str): end = __import__("datetime").datetime.fromisoformat(end)
        if start.tzinfo is None: start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None: end = end.replace(tzinfo=timezone.utc)
        zone = ZoneInfo(row["tutor_timezone"])
        description = "Meeting Details: " + (row["meeting_details_snapshot"] or "Pending")
        if row["focus"]: description += "\nBooking Focus: " + row["focus"]
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Tutoring Platform//Booking//EN",
                 f"X-WR-TIMEZONE:{row['tutor_timezone']}", "BEGIN:VEVENT", f"UID:{booking_id}@tutoring-platform",
                 f"DTSTART;TZID={row['tutor_timezone']}:{start.astimezone(zone):%Y%m%dT%H%M%S}",
                 f"DTEND;TZID={row['tutor_timezone']}:{end.astimezone(zone):%Y%m%dT%H%M%S}",
                 "SUMMARY:Tutoring session", f"DESCRIPTION:{escape(description)}", "STATUS:CONFIRMED", "END:VEVENT", "END:VCALENDAR", ""]
        return f"tutoring-session-{start.astimezone(zone):%Y-%m-%d}.ics", "\r\n".join(lines)
