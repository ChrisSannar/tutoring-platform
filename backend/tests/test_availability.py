from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.authentication import issue_magic_link
from app.config import get_settings
from app.main import create_app


async def availability_clients(monkeypatch, tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'availability.sqlite3'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO accounts (id, email, role, display_name) VALUES "
            "('tutor', 'tutor@example.com', 'tutor', NULL), "
            "('student', 'student@example.com', 'student', 'Student')"
        ))
    engine.dispose()
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    get_settings.cache_clear()
    application = create_app()
    application.state.context.now = lambda: datetime(2026, 7, 19, 8, tzinfo=timezone.utc)
    transport = httpx.ASGITransport(app=application)

    async def authenticated(email: str):
        client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
        token = issue_magic_link(database_url, email, 900)
        response = await client.post("/api/auth/magic-links/confirm", json={"token": token})
        return client, response.json()["csrf_token"]

    tutor, tutor_csrf = await authenticated("tutor@example.com")
    student, _ = await authenticated("student@example.com")
    return tutor, tutor_csrf, student, database_url


@pytest.mark.anyio
async def test_slots_are_anchored_blocked_and_privacy_preserving(monkeypatch, tmp_path: Path) -> None:
    tutor, csrf, student, _ = await availability_clients(monkeypatch, tmp_path)
    try:
        created = await tutor.post(
            "/api/tutor/availability-windows",
            headers={"Origin": "http://testserver", "X-CSRF-Token": csrf},
            json={"weekday": 0, "start_time": "09:00", "end_time": "11:30"},
        )
        blocked = await tutor.post(
            "/api/tutor/blocked-times",
            headers={"Origin": "http://testserver", "X-CSRF-Token": csrf},
            json={
                "start_at": "2026-07-20T15:00:00Z",
                "end_at": "2026-07-20T16:00:00Z",
                "reason": "Private appointment",
            },
        )
        slots = await student.get("/api/student/bookable-slots")
        denied = await student.get("/api/tutor/availability-windows")
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert created.status_code == blocked.status_code == 201
    assert slots.status_code == 200
    assert slots.json()["tutor_timezone"] == "America/Chicago"
    assert slots.json()["slots"][0] == {
        "start_at": "2026-07-20T14:00:00Z",
        "end_at": "2026-07-20T15:00:00Z",
    }
    assert all("reason" not in slot for slot in slots.json()["slots"])
    assert denied.status_code == 401
