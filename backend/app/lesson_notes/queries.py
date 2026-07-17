import re
from hashlib import sha256

from sqlalchemy import create_engine, text


def shared_notes(database_url: str, raw_session: str) -> list[dict]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(
                "SELECT lesson_notes.id, booking_id, title, markdown_source, date(bookings.start_at) AS booking_date "
                "FROM lesson_notes JOIN bookings ON bookings.id = booking_id JOIN authentication_sessions ON "
                "authentication_sessions.account_id = bookings.student_account_id WHERE session_hash = :hash "
                "AND published_at IS NOT NULL AND lesson_notes.deleted_at IS NULL ORDER BY bookings.start_at DESC"
            ), {"hash": sha256(raw_session.encode()).hexdigest()}).mappings()
            return [{**dict(row), "status": "published"} for row in rows]
    finally:
        engine.dispose()


def tutor_student_notes(database_url: str, student_id: str) -> list[dict]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(
                "SELECT lesson_notes.id, booking_id, title, markdown_source, published_at FROM lesson_notes "
                "JOIN bookings ON bookings.id = booking_id WHERE student_account_id = :student "
                "AND lesson_notes.deleted_at IS NULL ORDER BY bookings.start_at DESC"
            ), {"student": student_id}).mappings()
            return [{"id": row["id"], "booking_id": row["booking_id"], "title": row["title"],
                     "markdown_source": row["markdown_source"], "status": "published" if row["published_at"] else "draft"}
                    for row in rows]
    finally:
        engine.dispose()


def tutor_note_workspace(database_url: str, student_id: str, now) -> list[dict]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(
                "SELECT bookings.id AS booking_id, date(bookings.start_at) AS booking_date, lesson_notes.id AS note_id, "
                "title, markdown_source, published_at FROM bookings LEFT JOIN lesson_notes ON lesson_notes.booking_id = "
                "bookings.id AND lesson_notes.deleted_at IS NULL WHERE student_account_id = :student AND "
                "bookings.status != 'cancelled' AND bookings.end_at <= :now ORDER BY bookings.start_at DESC"
            ), {"student": student_id, "now": now}).mappings()
            return [{"booking_id": row["booking_id"], "booking_date": row["booking_date"], "note": None if row["note_id"] is None else
                     {"id": row["note_id"], "booking_id": row["booking_id"], "title": row["title"], "markdown_source": row["markdown_source"],
                      "status": "published" if row["published_at"] else "draft"}} for row in rows]
    finally:
        engine.dispose()


def download_note(database_url: str, raw_session: str, booking_id: str) -> tuple[str, str] | None:
    notes = [note for note in shared_notes(database_url, raw_session) if note["booking_id"] == booking_id]
    if not notes: return None
    note = notes[0]
    slug = re.sub(r"[^a-z0-9]+", "-", note["title"].lower()).strip("-") or "lesson-note"
    return f"{note['booking_date']}-{slug}.md", note["markdown_source"]
