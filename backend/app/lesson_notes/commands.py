from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, text


def response(row) -> dict:
    return {"id": row["id"], "booking_id": row["booking_id"], "title": row["title"],
            "markdown_source": row["markdown_source"], "status": "published" if row["published_at"] else "draft"}


def save_note(database_url: str, booking_id: str, title: str, source: str, now: datetime) -> dict | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            eligible = connection.execute(text(
                "SELECT 1 FROM bookings WHERE id = :id AND status != 'cancelled' AND end_at <= :now"
            ), {"id": booking_id, "now": now}).first()
            if eligible is None: return None
            existing = connection.execute(text(
                "SELECT id FROM lesson_notes WHERE booking_id = :booking AND deleted_at IS NULL"
            ), {"booking": booking_id}).scalar()
            if existing is None:
                note_id = str(uuid4())
                row = connection.execute(text(
                    "INSERT INTO lesson_notes (id, booking_id, title, markdown_source, updated_at) "
                    "VALUES (:id, :booking, :title, :source, :now) RETURNING *"
                ), {"id": note_id, "booking": booking_id, "title": title, "source": source, "now": now}).mappings().one()
            else:
                row = connection.execute(text(
                    "UPDATE lesson_notes SET title = :title, markdown_source = :source, updated_at = :now "
                    "WHERE id = :id RETURNING *"
                ), {"id": existing, "title": title, "source": source, "now": now}).mappings().one()
            return response(row)
    finally:
        engine.dispose()


def publish_note(database_url: str, booking_id: str, now: datetime) -> dict | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            row = connection.execute(text(
                "UPDATE lesson_notes SET published_at = COALESCE(published_at, :now), updated_at = :now "
                "WHERE booking_id = :booking AND deleted_at IS NULL RETURNING *"
            ), {"booking": booking_id, "now": now}).mappings().first()
            return None if row is None else response(row)
    finally:
        engine.dispose()


def delete_note(database_url: str, booking_id: str, now: datetime) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            return connection.execute(text(
                "UPDATE lesson_notes SET title = '[deleted]', markdown_source = '', deleted_at = :now, "
                "updated_at = :now WHERE booking_id = :booking AND deleted_at IS NULL"
            ), {"booking": booking_id, "now": now}).rowcount == 1
    finally:
        engine.dispose()
