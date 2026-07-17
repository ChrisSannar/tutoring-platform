from datetime import time
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


def update_window(database_url: str, window_id: str, weekday: int, start: time, end: time) -> dict | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            row = connection.execute(text(
                "UPDATE availability_windows SET weekday = :weekday, start_time = :start, "
                "end_time = :end WHERE id = :id RETURNING id, weekday, start_time, end_time"
            ), {"id": window_id, "weekday": weekday, "start": start.strftime("%H:%M"), "end": end.strftime("%H:%M")}).mappings().first()
            return None if row is None else dict(row)
    finally:
        engine.dispose()


def delete_window(database_url: str, window_id: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            result = connection.execute(text(
                "DELETE FROM availability_windows WHERE id = :id"
            ), {"id": window_id})
            return result.rowcount == 1
    finally:
        engine.dispose()
