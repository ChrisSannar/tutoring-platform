from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.availability import derive_bookable_slots
from app.database import db_connection
from app.occupancy import interval_is_free, utc_aware


def reconcile_past_bookings(connection, now: datetime) -> None:
    for booking in connection.execute(
        text(
            "SELECT id, student_account_id, funding_kind FROM bookings "
            "WHERE status = 'upcoming' AND end_at <= :now"
        ),
        {"now": utc_aware(now)},
    ).mappings():
        if booking["funding_kind"] == "session_credit":
            connection.execute(
                text(
                    "INSERT OR IGNORE INTO credit_ledger_entries "
                    "(id, student_account_id, event_type, quantity, reason, "
                    "idempotency_key, created_at) VALUES "
                    "(:id, :student, 'credit_booking_completion', 1, "
                    "'Past Booking replenishment', :key, :now)"
                ),
                {
                    "id": str(uuid4()),
                    "student": booking["student_account_id"],
                    "key": f"booking:{booking['id']}:completion",
                    "now": now,
                },
            )
        connection.execute(
            text("UPDATE bookings SET status = 'past' WHERE id = :id AND status = 'upcoming'"),
            {"id": booking["id"]},
        )


def account_id(connection, raw_session: str) -> str | None:
    return connection.execute(
        text(
            "SELECT account_id FROM authentication_sessions JOIN accounts "
            "ON accounts.id = account_id WHERE session_hash = :hash "
            "AND revoked_at IS NULL AND accounts.role = 'student'"
        ),
        {"hash": sha256(raw_session.encode()).hexdigest()},
    ).scalar()


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
    return any(slot["start_at"] == utc_aware(start) for slot in slots)


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
        upcoming = connection.execute(
            text(
                "SELECT 1 FROM bookings WHERE student_account_id = :student "
                "AND status = 'upcoming' AND (:booking IS NULL OR id != :booking)"
            ),
            {"student": student_id, "booking": exclude_booking_id},
        ).first()
    return (
        interval_is_free(
            connection,
            start,
            end,
            now,
            exclude_booking_id=exclude_booking_id,
        )
        and upcoming is None
    )


def settings_snapshot(connection) -> dict:
    return dict(
        connection.execute(
            text(
                "SELECT tutor_timezone, default_meeting_details "
                "FROM tutor_settings WHERE id = 1"
            )
        ).mappings().one()
    )


def booking_response(row) -> dict:
    return {
        "id": row["id"],
        "start_at": row["start_at"],
        "end_at": row["end_at"],
        "duration_minutes": 60,
        "tutor_timezone": row["tutor_timezone"],
        "funding_kind": row["funding_kind"],
        "focus": row["focus"],
        "meeting_details": row["meeting_details_snapshot"],
        "status": row["status"],
    }


def owned_booking(connection, booking_id: str, raw_session: str):
    return connection.execute(
        text(
            "SELECT bookings.*, tutor_timezone FROM bookings "
            "JOIN authentication_sessions ON authentication_sessions.account_id = "
            "bookings.student_account_id JOIN tutor_settings ON tutor_settings.id = 1 "
            "WHERE bookings.id = :id AND session_hash = :hash"
        ),
        {"id": booking_id, "hash": sha256(raw_session.encode()).hexdigest()},
    ).mappings().first()


def tutor_booking(connection, booking_id: str):
    return connection.execute(
        text(
            "SELECT bookings.*, tutor_timezone FROM bookings "
            "JOIN tutor_settings ON tutor_settings.id = 1 WHERE bookings.id = :id"
        ),
        {"id": booking_id},
    ).mappings().first()


def receipt_exists(connection, booking_id: str, key: str, kind: str) -> bool:
    return connection.execute(
        text(
            "SELECT 1 FROM booking_change_receipts WHERE booking_id = :booking "
            "AND idempotency_key = :key AND kind = :kind"
        ),
        {"booking": booking_id, "key": key, "kind": kind},
    ).first() is not None


def add_receipt(connection, booking_id: str, key: str, kind: str, now: datetime) -> None:
    connection.execute(
        text(
            "INSERT INTO booking_change_receipts "
            "(id, booking_id, kind, idempotency_key, created_at) "
            "VALUES (:id, :booking, :kind, :key, :now)"
        ),
        {
            "id": str(uuid4()),
            "booking": booking_id,
            "kind": kind,
            "key": key,
            "now": now,
        },
    )


def insert_booking(
    connection,
    student_id: str,
    start: datetime,
    focus: str | None,
    funding: str,
    key: str,
    now: datetime,
    settings: dict,
) -> dict:
    booking = {
        "id": str(uuid4()),
        "student": student_id,
        "start": start,
        "end": start + timedelta(hours=1),
        "focus": focus,
        "funding": funding,
        "details": settings["default_meeting_details"],
        "key": key,
        "now": now,
    }
    connection.execute(
        text(
            "INSERT INTO bookings "
            "(id, student_account_id, start_at, end_at, status, funding_kind, "
            "focus, meeting_details_snapshot, idempotency_key, created_at) VALUES "
            "(:id, :student, :start, :end, 'upcoming', :funding, :focus, "
            ":details, :key, :now)"
        ),
        booking,
    )
    return booking_response(
        {
            "id": booking["id"],
            "start_at": booking["start"],
            "end_at": booking["end"],
            "funding_kind": funding,
            "focus": focus,
            "meeting_details_snapshot": booking["details"],
            "tutor_timezone": settings["tutor_timezone"],
            "status": "upcoming",
        }
    )


def update_meeting_details(
    database_url: str, booking_id: str, details: str | None, now: datetime
) -> dict | None:
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        row = connection.execute(
            text(
                "UPDATE bookings SET meeting_details_snapshot = :details "
                "WHERE id = :id AND status = 'upcoming' RETURNING *"
            ),
            {"id": booking_id, "details": details},
        ).mappings().first()
        if row is None:
            return None
        return booking_response(
            {
                **dict(row),
                "tutor_timezone": connection.execute(
                    text("SELECT tutor_timezone FROM tutor_settings WHERE id = 1")
                ).scalar_one(),
            }
        )


def move_booking(
    database_url: str,
    booking_id: str,
    start: datetime,
    now: datetime,
    override_id: str | None,
    acknowledged: bool,
) -> dict | None:
    start = utc_aware(start)
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        normal = valid_slot(
            connection, database_url, start, now, exclude_booking_id=booking_id
        )
        booking = connection.execute(
            text("SELECT 1 FROM bookings WHERE id = :id AND status = 'upcoming'"),
            {"id": booking_id},
        ).first()
        override = (
            None
            if override_id is None
            else connection.execute(
                text(
                    "SELECT 1 FROM tutor_overrides WHERE id = :id AND start_at = :start"
                ),
                {"id": override_id, "start": start},
            ).first()
        )
        end = start + timedelta(hours=1)
        if (
            booking is None
            or not no_conflict(
                connection, None, start, end, now, exclude_booking_id=booking_id
            )
            or not (normal or (override is not None and acknowledged))
        ):
            return None
        row = connection.execute(
            text(
                "UPDATE bookings SET start_at = :start, end_at = :end "
                "WHERE id = :id RETURNING *"
            ),
            {"id": booking_id, "start": start, "end": end},
        ).mappings().one()
        return booking_response(
            {
                **dict(row),
                "tutor_timezone": connection.execute(
                    text("SELECT tutor_timezone FROM tutor_settings WHERE id = 1")
                ).scalar_one(),
            }
        )


def reschedule_student_booking(
    database_url: str,
    raw_session: str,
    booking_id: str,
    start: datetime,
    key: str,
    now: datetime,
) -> dict | None:
    start = utc_aware(start)
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        booking = owned_booking(connection, booking_id, raw_session)
        if booking is None:
            return None
        if receipt_exists(connection, booking_id, key, "reschedule"):
            return booking_response(booking)
        if (
            booking["status"] != "upcoming"
            or utc_aware(booking["start_at"]) - utc_aware(now) < timedelta(hours=24)
            or not valid_slot(
                connection, database_url, start, now, exclude_booking_id=booking_id
            )
        ):
            return None
        end = start + timedelta(hours=1)
        if not no_conflict(
            connection,
            booking["student_account_id"],
            start,
            end,
            now,
            exclude_booking_id=booking_id,
        ):
            return None
        connection.execute(
            text("UPDATE bookings SET start_at = :start, end_at = :end WHERE id = :id"),
            {"id": booking_id, "start": start, "end": end},
        )
        add_receipt(connection, booking_id, key, "reschedule", now)
        return booking_response({**dict(booking), "start_at": start, "end_at": end})


def create_student_booking(
    database_url: str,
    raw_session: str,
    start: datetime,
    focus: str | None,
    key: str,
    now: datetime,
) -> dict | None:
    start = utc_aware(start)
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        student_id = account_id(connection, raw_session)
        if student_id is None:
            return None
        existing = connection.execute(
            text(
                "SELECT bookings.*, tutor_timezone FROM bookings, tutor_settings "
                "WHERE idempotency_key = :key AND student_account_id = :student "
                "AND tutor_settings.id = 1"
            ),
            {"key": key, "student": student_id},
        ).mappings().first()
        if existing is not None:
            return booking_response(existing)
        end = start + timedelta(hours=1)
        if (
            not valid_slot(connection, database_url, start, now)
            or not no_conflict(connection, student_id, start, end, now)
        ):
            return None
        credits = connection.execute(
            text(
                "SELECT COALESCE(SUM(quantity), 0) FROM credit_ledger_entries "
                "WHERE student_account_id = :student "
                "AND event_type LIKE 'credit_%'"
            ),
            {"student": student_id},
        ).scalar_one()
        if credits < 1:
            return None
        created = insert_booking(
            connection,
            student_id,
            start,
            focus,
            "session_credit",
            key,
            now,
            settings_snapshot(connection),
        )
        connection.execute(
            text(
                "INSERT INTO credit_ledger_entries "
                "(id, student_account_id, event_type, quantity, reason, "
                "idempotency_key, created_at) VALUES "
                "(:id, :student, 'credit_booking_redemption', -1, "
                "'Booking funding', :key, :now)"
            ),
            {
                "id": str(uuid4()),
                "student": student_id,
                "key": f"booking:{created['id']}:redemption",
                "now": now,
            },
        )
        return created


def create_complimentary_booking(
    database_url: str,
    student_id: str,
    start: datetime,
    focus: str | None,
    key: str,
    now: datetime,
    override_id: str | None,
    warning_acknowledged: bool,
) -> dict | None:
    start = utc_aware(start)
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        existing = connection.execute(
            text(
                "SELECT bookings.*, tutor_timezone FROM bookings, tutor_settings "
                "WHERE idempotency_key = :key AND tutor_settings.id = 1"
            ),
            {"key": key},
        ).mappings().first()
        if existing is not None:
            return booking_response(existing)
        normal_slot = valid_slot(connection, database_url, start, now)
        override = (
            None
            if override_id is None
            else connection.execute(
                text(
                    "SELECT 1 FROM tutor_overrides WHERE id = :id AND start_at = :start"
                ),
                {"id": override_id, "start": start},
            ).first()
        )
        end = start + timedelta(hours=1)
        if (
            not (normal_slot or (override is not None and warning_acknowledged))
            or connection.execute(
                text("SELECT 1 FROM accounts WHERE id = :id AND role = 'student'"),
                {"id": student_id},
            ).first()
            is None
            or not no_conflict(connection, student_id, start, end, now)
        ):
            return None
        return insert_booking(
            connection,
            student_id,
            start,
            focus,
            "complimentary",
            key,
            now,
            settings_snapshot(connection),
        )


def cancel_booking(
    database_url: str,
    booking_id: str,
    key: str,
    now: datetime,
    raw_session: str | None = None,
) -> dict | None:
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        booking = (
            tutor_booking(connection, booking_id)
            if raw_session is None
            else owned_booking(connection, booking_id, raw_session)
        )
        if booking is None:
            return None
        if receipt_exists(connection, booking_id, key, "cancel"):
            return booking_response(booking)
        if booking["status"] != "upcoming":
            return None
        if booking["funding_kind"] == "session_credit":
            connection.execute(
                text(
                    "INSERT OR IGNORE INTO credit_ledger_entries "
                    "(id, student_account_id, event_type, quantity, reason, "
                    "idempotency_key, created_at) VALUES "
                    "(:id, :student, 'credit_booking_cancellation', 1, "
                    "'Booking cancellation restoration', :key, :now)"
                ),
                {
                    "id": str(uuid4()),
                    "student": booking["student_account_id"],
                    "key": f"booking:{booking_id}:cancellation",
                    "now": now,
                },
            )
        connection.execute(
            text("UPDATE bookings SET status = 'cancelled' WHERE id = :id"),
            {"id": booking_id},
        )
        add_receipt(connection, booking_id, key, "cancel", now)
        return booking_response({**dict(booking), "status": "cancelled"})


def upcoming_booking(
    database_url: str, raw_session: str, now: datetime
) -> dict | None:
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        row = connection.execute(
            text(
                "SELECT bookings.*, tutor_timezone FROM bookings "
                "JOIN authentication_sessions ON authentication_sessions.account_id = "
                "bookings.student_account_id JOIN tutor_settings ON tutor_settings.id = 1 "
                "WHERE session_hash = :hash AND status = 'upcoming'"
            ),
            {"hash": sha256(raw_session.encode()).hexdigest()},
        ).mappings().first()
        return None if row is None else booking_response(row)


def tutor_calendar(database_url: str, now: datetime) -> list[dict]:
    with db_connection(database_url, mode="immediate") as connection:
        reconcile_past_bookings(connection, now)
        rows = connection.execute(
            text(
                "SELECT bookings.*, tutor_timezone, accounts.id AS student_id, "
                "accounts.display_name, accounts.email FROM bookings "
                "JOIN accounts ON accounts.id = student_account_id "
                "JOIN tutor_settings ON tutor_settings.id = 1 ORDER BY start_at"
            )
        ).mappings()
        return [
            {
                **booking_response(row),
                "student": {
                    "id": row["student_id"],
                    "display_name": row["display_name"],
                    "email": row["email"],
                },
            }
            for row in rows
        ]


def escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def booking_calendar_export(
    database_url: str, raw_session: str, booking_id: str
) -> tuple[str, str] | None:
    with db_connection(database_url, mode="read") as connection:
        row = connection.execute(
            text(
                "SELECT bookings.*, tutor_timezone FROM bookings "
                "JOIN authentication_sessions ON authentication_sessions.account_id = "
                "student_account_id JOIN tutor_settings ON tutor_settings.id = 1 "
                "WHERE bookings.id = :id AND session_hash = :hash "
                "AND status = 'upcoming'"
            ),
            {
                "id": booking_id,
                "hash": sha256(raw_session.encode()).hexdigest(),
            },
        ).mappings().first()
        if row is None:
            return None
        start, end = utc_aware(row["start_at"]), utc_aware(row["end_at"])
        zone = ZoneInfo(row["tutor_timezone"])
        description = "Meeting Details: " + (
            row["meeting_details_snapshot"] or "Pending"
        )
        if row["focus"]:
            description += "\nBooking Focus: " + row["focus"]
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Tutoring Platform//Booking//EN",
            f"X-WR-TIMEZONE:{row['tutor_timezone']}",
            "BEGIN:VEVENT",
            f"UID:{booking_id}@tutoring-platform",
            f"DTSTART;TZID={row['tutor_timezone']}:{start.astimezone(zone):%Y%m%dT%H%M%S}",
            f"DTEND;TZID={row['tutor_timezone']}:{end.astimezone(zone):%Y%m%dT%H%M%S}",
            "SUMMARY:Tutoring session",
            f"DESCRIPTION:{escape(description)}",
            "STATUS:CONFIRMED",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ]
        return (
            f"tutoring-session-{start.astimezone(zone):%Y-%m-%d}.ics",
            "\r\n".join(lines),
        )
