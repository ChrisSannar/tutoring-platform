from datetime import timezone
from hashlib import sha256
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text


def escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def booking_calendar_export(database_url: str, raw_session: str, booking_id: str) -> tuple[str, str] | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
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
    finally:
        engine.dispose()
