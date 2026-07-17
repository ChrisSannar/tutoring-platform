import asyncio
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


async def booking_context(monkeypatch, tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'bookings.sqlite3'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO accounts (id, email, role, display_name) VALUES "
            "('tutor', 'tutor@example.com', 'tutor', NULL), "
            "('student', 'student@example.com', 'student', 'Student'), "
            "('student-2', 'second@example.com', 'student', 'Second Student')"
        ))
        connection.execute(text(
            "INSERT INTO availability_windows (id, weekday, start_time, end_time) "
            "VALUES ('monday', 0, '09:00', '12:00')"
        ))
        connection.execute(text(
            "INSERT INTO credit_ledger_entries (id, student_account_id, event_type, quantity, reason, idempotency_key, created_at) VALUES "
            "('promotion', 'student', 'promotion_granted', 1, NULL, 'promotion', CURRENT_TIMESTAMP), "
            "('credit', 'student', 'credit_adjustment', 1, 'Prepaid', 'credit', CURRENT_TIMESTAMP)"
        ))
        connection.execute(text(
            "UPDATE tutor_settings SET default_meeting_details = 'Initial meeting room' WHERE id = 1"
        ))
    engine.dispose()
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    get_settings.cache_clear()
    app = create_app()
    app.state.context.now = lambda: datetime(2026, 7, 19, 8, tzinfo=timezone.utc)
    transport = httpx.ASGITransport(app=app)

    async def authenticate(email: str):
        client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
        token = issue_magic_link(database_url, email, 900)
        response = await client.post("/api/auth/magic-links/confirm", json={"token": token})
        return client, response.json()["csrf_token"]

    tutor, tutor_csrf = await authenticate("tutor@example.com")
    student, student_csrf = await authenticate("student@example.com")
    return tutor, tutor_csrf, student, student_csrf, database_url


@pytest.mark.anyio
async def test_promotion_then_credit_booking_snapshots_settings(monkeypatch, tmp_path: Path) -> None:
    tutor, tutor_csrf, student, student_csrf, database_url = await booking_context(monkeypatch, tmp_path)
    student_headers = {"Origin": "http://testserver", "X-CSRF-Token": student_csrf, "Idempotency-Key": "first-booking"}
    try:
        promotion = await student.post(
            "/api/student/bookings", headers=student_headers,
            json={"start_at": "2026-07-20T14:00:00Z", "focus": "Quadratic equations", "confirmed": True},
        )
        retry = await student.post(
            "/api/student/bookings", headers=student_headers,
            json={"start_at": "2026-07-20T14:00:00Z", "focus": "Quadratic equations", "confirmed": True},
        )
        funding_after_promotion = await student.get("/api/student/funding")
        await tutor.put(
            "/api/tutor/settings",
            headers={"Origin": "http://testserver", "X-CSRF-Token": tutor_csrf},
            json={"currency": "USD", "session_price_cents": 9000, "tutor_timezone": "America/Chicago", "default_meeting_details": "Changed room"},
        )
        unchanged = await student.get("/api/student/bookings/upcoming")
        engine = create_engine(database_url)
        with engine.begin() as connection:
            connection.execute(text("UPDATE bookings SET status = 'completed'"))
        engine.dispose()
        credit = await student.post(
            "/api/student/bookings",
            headers={**student_headers, "Idempotency-Key": "credit-booking"},
            json={"start_at": "2026-07-20T15:00:00Z", "focus": None, "confirmed": True},
        )
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert promotion.status_code == retry.status_code == 201
    assert promotion.json()["funding_kind"] == "first_session_promotion"
    assert retry.json()["id"] == promotion.json()["id"]
    assert funding_after_promotion.json() == {
        "first_session_promotion": "unavailable",
        "session_credits": 1,
    }
    assert unchanged.json()["meeting_details"] == "Initial meeting room"
    assert unchanged.json()["price_cents"] == 7500
    assert credit.status_code == 201
    assert credit.json()["funding_kind"] == "session_credit"
    assert credit.json()["meeting_details"] == "Changed room"
    assert credit.json()["price_cents"] == 9000


@pytest.mark.anyio
async def test_concurrent_booking_attempts_cannot_duplicate_slot_or_funding(monkeypatch, tmp_path: Path) -> None:
    tutor, _, student, student_csrf, _ = await booking_context(monkeypatch, tmp_path)
    base = {"Origin": "http://testserver", "X-CSRF-Token": student_csrf}
    try:
        first, second = await asyncio.gather(
            student.post(
                "/api/student/bookings",
                headers={**base, "Idempotency-Key": "concurrent-one"},
                json={"start_at": "2026-07-20T14:00:00Z", "focus": None, "confirmed": True},
            ),
            student.post(
                "/api/student/bookings",
                headers={**base, "Idempotency-Key": "concurrent-two"},
                json={"start_at": "2026-07-20T14:00:00Z", "focus": None, "confirmed": True},
            ),
        )
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert sorted([first.status_code, second.status_code]) == [201, 409]


@pytest.mark.anyio
async def test_tutor_creates_explicit_complimentary_booking_without_funding(monkeypatch, tmp_path: Path) -> None:
    tutor, tutor_csrf, student, _, _ = await booking_context(monkeypatch, tmp_path)
    try:
        created = await tutor.post(
            "/api/tutor/students/student-2/bookings",
            headers={"Origin": "http://testserver", "X-CSRF-Token": tutor_csrf, "Idempotency-Key": "gift"},
            json={"start_at": "2026-07-20T16:00:00Z", "focus": "Tutor gift", "complimentary": True},
        )
        student_denied = await student.post(
            "/api/tutor/students/student-2/bookings",
            headers={"Origin": "http://testserver", "X-CSRF-Token": tutor_csrf, "Idempotency-Key": "denied"},
            json={"start_at": "2026-07-20T16:00:00Z", "focus": None, "complimentary": True},
        )
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert created.status_code == 201
    assert created.json()["funding_kind"] == "complimentary"
    assert student_denied.status_code == 403


@pytest.mark.anyio
async def test_override_requires_warning_and_unfunded_student_cannot_book(monkeypatch, tmp_path: Path) -> None:
    tutor, tutor_csrf, student, _, database_url = await booking_context(monkeypatch, tmp_path)
    tutor_headers = {"Origin": "http://testserver", "X-CSRF-Token": tutor_csrf}
    second_app = create_app()
    second_app.state.context.now = lambda: datetime(2026, 7, 19, 8, tzinfo=timezone.utc)
    second = httpx.AsyncClient(transport=httpx.ASGITransport(app=second_app), base_url="http://testserver")
    token = issue_magic_link(database_url, "second@example.com", 900)
    second_auth = await second.post("/api/auth/magic-links/confirm", json={"token": token})
    second_headers = {"Origin": "http://testserver", "X-CSRF-Token": second_auth.json()["csrf_token"], "Idempotency-Key": "unfunded"}
    try:
        unfunded = await second.post(
            "/api/student/bookings", headers=second_headers,
            json={"start_at": "2026-07-20T14:00:00Z", "focus": None, "confirmed": True},
        )
        override = await tutor.post(
            "/api/tutor/overrides", headers=tutor_headers,
            json={"start_at": "2026-09-20T15:00:00Z", "warning": "Outside normal policy"},
        )
        without_warning = await tutor.post(
            "/api/tutor/students/student-2/bookings",
            headers={**tutor_headers, "Idempotency-Key": "override-no-warning"},
            json={"start_at": "2026-09-20T15:00:00Z", "focus": None, "complimentary": True, "override_id": override.json()["id"]},
        )
        with_warning = await tutor.post(
            "/api/tutor/students/student-2/bookings",
            headers={**tutor_headers, "Idempotency-Key": "override-warning"},
            json={"start_at": "2026-09-20T15:00:00Z", "focus": None, "complimentary": True, "override_id": override.json()["id"], "warning_acknowledged": True},
        )
    finally:
        await tutor.aclose()
        await student.aclose()
        await second.aclose()
        get_settings.cache_clear()

    assert unfunded.status_code == 409
    assert without_warning.status_code == 409
    assert with_warning.status_code == 201


@pytest.mark.anyio
async def test_tutor_calendar_edits_and_moves_booking_without_changing_funding(monkeypatch, tmp_path: Path) -> None:
    tutor, tutor_csrf, student, student_csrf, database_url = await booking_context(monkeypatch, tmp_path)
    tutor_headers = {"Origin": "http://testserver", "X-CSRF-Token": tutor_csrf}
    try:
        created = await student.post(
            "/api/student/bookings",
            headers={"Origin": "http://testserver", "X-CSRF-Token": student_csrf, "Idempotency-Key": "calendar-booking"},
            json={"start_at": "2026-07-20T14:00:00Z", "focus": "Fractions", "confirmed": True},
        )
        calendar = await tutor.get("/api/tutor/bookings")
        booking_id = created.json()["id"]
        details = await tutor.put(
            f"/api/tutor/bookings/{booking_id}/meeting-details", headers=tutor_headers,
            json={"meeting_details": "123 Main Street"},
        )
        moved = await tutor.put(
            f"/api/tutor/bookings/{booking_id}/schedule", headers=tutor_headers,
            json={"start_at": "2026-07-20T15:00:00Z"},
        )
        await tutor.post(
            "/api/tutor/students/student-2/bookings",
            headers={**tutor_headers, "Idempotency-Key": "occupied"},
            json={"start_at": "2026-07-20T16:00:00Z", "focus": None, "complimentary": True},
        )
        conflict = await tutor.put(
            f"/api/tutor/bookings/{booking_id}/schedule", headers=tutor_headers,
            json={"start_at": "2026-07-20T16:00:00Z"},
        )
        override = await tutor.post(
            "/api/tutor/overrides", headers=tutor_headers,
            json={"start_at": "2026-09-20T15:00:00Z", "warning": "Outside normal policy"},
        )
        unacknowledged = await tutor.put(
            f"/api/tutor/bookings/{booking_id}/schedule", headers=tutor_headers,
            json={"start_at": "2026-09-20T15:00:00Z", "override_id": override.json()["id"]},
        )
        overridden = await tutor.put(
            f"/api/tutor/bookings/{booking_id}/schedule", headers=tutor_headers,
            json={"start_at": "2026-09-20T15:00:00Z", "override_id": override.json()["id"], "warning_acknowledged": True},
        )
        denied = await student.get("/api/tutor/bookings")
        engine = create_engine(database_url)
        with engine.connect() as connection:
            funding_events = connection.execute(text(
                "SELECT event_type, quantity FROM credit_ledger_entries WHERE student_account_id = 'student' ORDER BY created_at, id"
            )).all()
        engine.dispose()
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert calendar.json()["bookings"][0]["student"]["display_name"] == "Student"
    assert details.json()["meeting_details"] == "123 Main Street"
    assert moved.json()["funding_kind"] == "first_session_promotion"
    assert conflict.status_code == 409
    assert unacknowledged.status_code == 409
    assert overridden.status_code == 200
    assert overridden.json()["funding_kind"] == "first_session_promotion"
    assert denied.status_code == 401
    assert [event for event in funding_events if event[0] == "promotion_consumed"] == [("promotion_consumed", -1)]
