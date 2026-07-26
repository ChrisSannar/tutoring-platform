from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import text

from app.database import db_connection


def create_override(database_url: str, start: datetime, warning: str) -> dict:
    override = {"id": str(uuid4()), "start_at": start, "end_at": start + timedelta(hours=1), "warning": warning}
    with db_connection(database_url) as connection:
        connection.execute(text(
            "INSERT INTO tutor_overrides (id, start_at, end_at, warning) "
            "VALUES (:id, :start_at, :end_at, :warning)"
        ), override)
    return {**override, "requires_booking_warning": True}


def list_overrides(database_url: str) -> list[dict]:
    with db_connection(database_url, mode="read") as connection:
        return [{**dict(row), "requires_booking_warning": True} for row in connection.execute(text(
            "SELECT id, start_at, end_at, warning FROM tutor_overrides ORDER BY start_at"
        )).mappings()]


def update_override(database_url: str, override_id: str, start: datetime, warning: str) -> dict | None:
    with db_connection(database_url) as connection:
        row = connection.execute(text(
            "UPDATE tutor_overrides SET start_at = :start, end_at = :end, warning = :warning "
            "WHERE id = :id RETURNING id, start_at, end_at, warning"
        ), {"id": override_id, "start": start, "end": start + timedelta(hours=1), "warning": warning}).mappings().first()
        return None if row is None else {**dict(row), "requires_booking_warning": True}


def delete_override(database_url: str, override_id: str) -> bool:
    with db_connection(database_url) as connection:
        return connection.execute(text(
            "DELETE FROM tutor_overrides WHERE id = :id"
        ), {"id": override_id}).rowcount == 1
