from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, text


def create_blocked_time(database_url: str, start: datetime, end: datetime, reason: str | None) -> dict:
    blocked = {"id": str(uuid4()), "start_at": start, "end_at": end, "reason": reason}
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO blocked_times (id, start_at, end_at, reason) "
                "VALUES (:id, :start_at, :end_at, :reason)"
            ), blocked)
        return blocked
    finally:
        engine.dispose()


def list_blocked_times(database_url: str) -> list[dict]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            return [dict(row) for row in connection.execute(text(
                "SELECT id, start_at, end_at, reason FROM blocked_times ORDER BY start_at"
            )).mappings()]
    finally:
        engine.dispose()


def update_blocked_time(database_url: str, blocked_id: str, start: datetime, end: datetime, reason: str | None) -> dict | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            row = connection.execute(text(
                "UPDATE blocked_times SET start_at = :start, end_at = :end, reason = :reason "
                "WHERE id = :id RETURNING id, start_at, end_at, reason"
            ), {"id": blocked_id, "start": start, "end": end, "reason": reason}).mappings().first()
            return None if row is None else dict(row)
    finally:
        engine.dispose()


def delete_blocked_time(database_url: str, blocked_id: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            return connection.execute(text(
                "DELETE FROM blocked_times WHERE id = :id"
            ), {"id": blocked_id}).rowcount == 1
    finally:
        engine.dispose()
