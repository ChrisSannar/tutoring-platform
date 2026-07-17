from pathlib import Path

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


@pytest.mark.anyio
async def test_historical_session_requests_are_dropped_not_converted(monkeypatch, tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'retirement.sqlite3'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "20260717_0016")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO accounts (id, email, role, display_name) VALUES "
            "('student', 'historical@example.com', 'student', 'Historical')"
        ))
        connection.execute(text(
            "INSERT INTO session_requests (id, student_account_id, service, preferred_start, timezone, status, "
            "idempotency_key) VALUES ('old-request', 'student', 'Historical service', "
            "'2026-07-20 14:00:00', 'America/Chicago', 'pending', 'old-key')"
        ))
    command.upgrade(config, "head")
    with engine.connect() as connection:
        old_table = connection.execute(text(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'session_requests'"
        )).scalar_one()
        bookings = connection.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()
    engine.dispose()

    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    get_settings.cache_clear()
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app()), base_url="http://testserver")
    try:
        student_route = await client.post("/api/student/session-requests", json={})
        tutor_route = await client.get("/api/tutor/session-requests")
    finally:
        await client.aclose(); get_settings.cache_clear()

    assert old_table == 0 and bookings == 0
    assert student_route.status_code == tutor_route.status_code == 404
