from pathlib import Path
from urllib.parse import parse_qs, urlparse

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


async def student_directory_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, role: str = "tutor"
) -> httpx.AsyncClient:
    database_url = f"sqlite:///{tmp_path / 'students.sqlite3'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role, display_name) VALUES "
                    "('tutor', 'tutor@example.com', 'tutor', NULL), "
                    "('student-a', 'avery@example.com', 'student', 'Avery Chen'), "
                    "('student-b', 'bailey@example.com', 'student', 'Bailey Jones')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO credit_ledger_entries (id, student_account_id, "
                    "event_type, quantity, reason, idempotency_key, created_at) VALUES "
                    "('promotion-a', 'student-a', 'promotion_granted', 1, NULL, "
                    "'promotion-a', CURRENT_TIMESTAMP)"
                )
            )
    finally:
        engine.dispose()
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    get_settings.cache_clear()
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://testserver"
    )
    email = "tutor@example.com" if role == "tutor" else "avery@example.com"
    await client.post("/api/auth/magic-links", json={"email": email})
    outbox = await client.get("/api/development/outbox")
    token = parse_qs(
        urlparse(outbox.json()["messages"][-1]["magic_link"]).query
    )["token"][0]
    await client.post("/api/auth/magic-links/confirm", json={"token": token})
    return client


@pytest.mark.anyio
async def test_tutor_reads_an_allowlisted_student_detail_with_bounded_summaries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await student_directory_client(monkeypatch, tmp_path)
    try:
        listed = await client.get("/api/tutor/students")
        detail = await client.get("/api/tutor/students/student-a")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert listed.json()["students"][0] == {
        "id": "student-a",
        "email": "avery@example.com",
        "display_name": "Avery Chen",
    }
    assert detail.json() == {
        "id": "student-a",
        "email": "avery@example.com",
        "display_name": "Avery Chen",
        "funding": {
            "first_session_promotion": "available",
            "session_credits": 0,
        },
        "pending_refund_requests": [],
        "upcoming_booking": None,
    }


@pytest.mark.anyio
async def test_student_cannot_read_the_tutor_student_directory_or_detail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await student_directory_client(monkeypatch, tmp_path, role="student-a")
    try:
        listed = await client.get("/api/tutor/students")
        detail = await client.get("/api/tutor/students/student-b")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert listed.status_code == 401
    assert detail.status_code == 401
    assert "bailey@example.com" not in detail.text
