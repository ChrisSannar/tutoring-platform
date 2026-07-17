from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, text


def create_override(database_url: str, start: datetime, warning: str) -> dict:
    override = {"id": str(uuid4()), "start_at": start, "end_at": start + timedelta(hours=1), "warning": warning}
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO tutor_overrides (id, start_at, end_at, warning) "
                "VALUES (:id, :start_at, :end_at, :warning)"
            ), override)
        return {**override, "requires_booking_warning": True}
    finally:
        engine.dispose()


def list_overrides(database_url: str) -> list[dict]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            return [{**dict(row), "requires_booking_warning": True} for row in connection.execute(text(
                "SELECT id, start_at, end_at, warning FROM tutor_overrides ORDER BY start_at"
            )).mappings()]
    finally:
        engine.dispose()


def delete_override(database_url: str, override_id: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            return connection.execute(text(
                "DELETE FROM tutor_overrides WHERE id = :id"
            ), {"id": override_id}).rowcount == 1
    finally:
        engine.dispose()
