import asyncio
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
        credit_change = await client.post(
            "/api/tutor/students/student-b/credits",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": client.cookies["tutoring_csrf"],
                "Idempotency-Key": "student-forbidden",
            },
            json={"quantity": 1, "reason": "Not allowed"},
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert listed.status_code == 401
    assert detail.status_code == 401
    assert credit_change.status_code == 403
    assert "bailey@example.com" not in detail.text


@pytest.mark.anyio
async def test_tutor_adjustments_append_an_idempotent_credit_ledger(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await student_directory_client(monkeypatch, tmp_path)
    base_headers = {
        "Origin": "http://testserver",
        "X-CSRF-Token": client.cookies["tutoring_csrf"],
    }
    try:
        granted = await client.post(
            "/api/tutor/students/student-a/credits",
            headers={**base_headers, "Idempotency-Key": "grant-two"},
            json={"quantity": 2, "reason": "Prepaid tutoring package"},
        )
        retried = await client.post(
            "/api/tutor/students/student-a/credits",
            headers={**base_headers, "Idempotency-Key": "grant-two"},
            json={"quantity": 2, "reason": "Prepaid tutoring package"},
        )
        deducted = await client.post(
            "/api/tutor/students/student-a/credits",
            headers={**base_headers, "Idempotency-Key": "deduct-one"},
            json={"quantity": -1, "reason": "Correct duplicate grant"},
        )
        detail = await client.get("/api/tutor/students/student-a")
        ledger = await client.get("/api/tutor/students/student-a/credit-ledger")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert granted.status_code == 200
    assert granted.json()["session_credits"] == 2
    assert retried.json() == granted.json()
    assert deducted.json()["session_credits"] == 1
    assert detail.json()["funding"]["session_credits"] == 1
    assert [event["quantity"] for event in ledger.json()["events"]] == [1, 2, -1]
    assert [event["event_type"] for event in ledger.json()["events"]] == [
        "promotion_granted",
        "credit_adjustment",
        "credit_adjustment",
    ]
    assert [event["reason"] for event in ledger.json()["events"]] == [
        None,
        "Prepaid tutoring package",
        "Correct duplicate grant",
    ]


@pytest.mark.anyio
async def test_credit_adjustments_require_reason_and_never_create_negative_value(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await student_directory_client(monkeypatch, tmp_path)
    headers = {
        "Origin": "http://testserver",
        "X-CSRF-Token": client.cookies["tutoring_csrf"],
    }
    try:
        missing_reason = await client.post(
            "/api/tutor/students/student-a/credits",
            headers={**headers, "Idempotency-Key": "missing-reason"},
            json={"quantity": 1, "reason": "   "},
        )
        too_large_deduction = await client.post(
            "/api/tutor/students/student-a/credits",
            headers={**headers, "Idempotency-Key": "negative"},
            json={"quantity": -1, "reason": "No available ordinary credit"},
        )
        detail = await client.get("/api/tutor/students/student-a")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert missing_reason.status_code == 422
    assert too_large_deduction.status_code == 409
    assert detail.json()["funding"]["session_credits"] == 0


@pytest.mark.anyio
async def test_concurrent_deductions_can_spend_one_credit_only_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await student_directory_client(monkeypatch, tmp_path)
    headers = {
        "Origin": "http://testserver",
        "X-CSRF-Token": client.cookies["tutoring_csrf"],
    }
    try:
        await client.post(
            "/api/tutor/students/student-a/credits",
            headers={**headers, "Idempotency-Key": "one-credit"},
            json={"quantity": 1, "reason": "One available credit"},
        )
        deductions = await asyncio.gather(
            client.post(
                "/api/tutor/students/student-a/credits",
                headers={**headers, "Idempotency-Key": "spend-a"},
                json={"quantity": -1, "reason": "First spend"},
            ),
            client.post(
                "/api/tutor/students/student-a/credits",
                headers={**headers, "Idempotency-Key": "spend-b"},
                json={"quantity": -1, "reason": "Competing spend"},
            ),
        )
        detail = await client.get("/api/tutor/students/student-a")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert sorted(response.status_code for response in deductions) == [200, 409]
    assert detail.json()["funding"]["session_credits"] == 0
