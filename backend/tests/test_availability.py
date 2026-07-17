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


@pytest.mark.anyio
async def test_tutor_edits_and_deletes_calendar_rules(monkeypatch, tmp_path: Path) -> None:
    tutor, csrf, student, _ = await availability_clients(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf}
    try:
        window = await tutor.post(
            "/api/tutor/availability-windows", headers=headers,
            json={"weekday": 1, "start_time": "10:00", "end_time": "12:00"},
        )
        changed_window = await tutor.put(
            f"/api/tutor/availability-windows/{window.json()['id']}", headers=headers,
            json={"weekday": 2, "start_time": "11:00", "end_time": "13:00"},
        )
        blocked = await tutor.post(
            "/api/tutor/blocked-times", headers=headers,
            json={"start_at": "2026-07-22T16:00:00Z", "end_at": "2026-07-22T17:00:00Z", "reason": "Original"},
        )
        changed_block = await tutor.put(
            f"/api/tutor/blocked-times/{blocked.json()['id']}", headers=headers,
            json={"start_at": "2026-07-22T17:00:00Z", "end_at": "2026-07-22T18:00:00Z", "reason": "Private change"},
        )
        listed_blocks = await tutor.get("/api/tutor/blocked-times")
        removed_window = await tutor.delete(
            f"/api/tutor/availability-windows/{window.json()['id']}", headers=headers
        )
        removed_block = await tutor.delete(
            f"/api/tutor/blocked-times/{blocked.json()['id']}", headers=headers
        )
        student_mutation = await student.post(
            "/api/tutor/availability-windows", headers=headers,
            json={"weekday": 1, "start_time": "10:00", "end_time": "12:00"},
        )
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert changed_window.json()["weekday"] == 2
    assert changed_block.json()["reason"] == "Private change"
    assert listed_blocks.json()[0]["reason"] == "Private change"
    assert removed_window.status_code == removed_block.status_code == 204
    assert student_mutation.status_code == 403


@pytest.mark.anyio
async def test_bookings_active_holds_and_policy_boundaries_remove_slots(monkeypatch, tmp_path: Path) -> None:
    tutor, csrf, student, database_url = await availability_clients(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf}
    try:
        await tutor.post(
            "/api/tutor/availability-windows", headers=headers,
            json={"weekday": 0, "start_time": "09:00", "end_time": "12:00"},
        )
        await tutor.post(
            "/api/tutor/availability-windows", headers=headers,
            json={"weekday": 6, "start_time": "09:00", "end_time": "10:00"},
        )
        engine = create_engine(database_url)
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO bookings (id, student_account_id, start_at, end_at, status, funding_kind, idempotency_key, created_at) "
                "VALUES ('booking', 'student', '2026-07-20 14:00:00', '2026-07-20 15:00:00', 'upcoming', 'complimentary', 'booking', CURRENT_TIMESTAMP)"
            ))
            connection.execute(text(
                "INSERT INTO slot_holds (id, student_account_id, start_at, end_at, expires_at) "
                "VALUES ('hold', 'student', '2026-07-20 15:00:00', '2026-07-20 16:00:00', '2026-07-20 12:00:00')"
            ))
        engine.dispose()
        slots = await student.get("/api/student/bookable-slots")
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    starts = [slot["start_at"] for slot in slots.json()["slots"]]
    assert "2026-07-20T14:00:00Z" not in starts
    assert "2026-07-20T15:00:00Z" not in starts
    assert "2026-07-20T16:00:00Z" in starts
    assert "2026-07-19T14:00:00Z" not in starts


@pytest.mark.anyio
async def test_tutor_override_records_an_explicit_booking_warning(monkeypatch, tmp_path: Path) -> None:
    tutor, csrf, student, _ = await availability_clients(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf}
    try:
        created = await tutor.post(
            "/api/tutor/overrides", headers=headers,
            json={"start_at": "2026-09-20T15:00:00Z", "warning": "Outside normal availability and horizon"},
        )
        listed = await tutor.get("/api/tutor/overrides")
        denied = await student.get("/api/tutor/overrides")
        removed = await tutor.delete(
            f"/api/tutor/overrides/{created.json()['id']}", headers=headers
        )
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert created.status_code == 201
    assert created.json()["requires_booking_warning"] is True
    assert listed.json()[0]["warning"] == "Outside normal availability and horizon"
    assert denied.status_code == 401
    assert removed.status_code == 204
