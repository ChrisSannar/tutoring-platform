from datetime import datetime, time
from uuid import uuid4

from sqlalchemy import create_engine, text


def create_window(database_url: str, weekday: int, start: time, end: time) -> dict:
    window = {"id": str(uuid4()), "weekday": weekday, "start_time": start.strftime("%H:%M"), "end_time": end.strftime("%H:%M")}
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO availability_windows (id, weekday, start_time, end_time) "
                "VALUES (:id, :weekday, :start_time, :end_time)"
            ), window)
        return window
    finally:
        engine.dispose()


def list_windows(database_url: str) -> list[dict]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(
                "SELECT id, weekday, start_time, end_time FROM availability_windows "
                "ORDER BY weekday, start_time"
            )).mappings()
            return [dict(row) for row in rows]
    finally:
        engine.dispose()


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
