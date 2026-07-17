from pathlib import Path
from urllib.parse import parse_qs, urlparse

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.authentication import issue_magic_link
from app.config import get_settings
from app.main import create_app


async def authenticated_tutor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[httpx.AsyncClient, str]:
    database_url = f"sqlite:///{tmp_path / 'tutor-settings.sqlite3'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role) "
                    "VALUES ('tutor-account', 'tutor@example.com', 'tutor')"
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
    await client.post("/api/auth/magic-links", json={"email": "tutor@example.com"})
    outbox = await client.get("/api/development/outbox")
    token = parse_qs(
        urlparse(outbox.json()["messages"][-1]["magic_link"]).query
    )["token"][0]
    authenticated = await client.post(
        "/api/auth/magic-links/confirm", json={"token": token}
    )
    return client, authenticated.json()["csrf_token"]


@pytest.mark.anyio
async def test_tutor_views_and_updates_authoritative_business_settings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor(monkeypatch, tmp_path)
    try:
        initial = await client.get("/api/tutor/settings")
        updated = await client.put(
            "/api/tutor/settings",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
            },
            json={
                "currency": "USD",
                "session_price_cents": 8250,
                "tutor_timezone": "America/New_York",
                "default_meeting_details": "https://meet.example.com/avery",
            },
        )
        current = await client.get("/api/tutor/settings")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert initial.json() == {
        "currency": "USD",
        "session_price_cents": 7500,
        "tutor_timezone": "America/Chicago",
        "default_meeting_details": None,
    }
    assert updated.status_code == 200
    assert current.json() == updated.json()
    assert current.json()["session_price_cents"] == 8250


@pytest.mark.anyio
async def test_settings_reject_invalid_or_untrusted_updates_without_partial_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor(monkeypatch, tmp_path)
    valid_payload = {
        "currency": "USD",
        "session_price_cents": 8250,
        "tutor_timezone": "America/New_York",
        "default_meeting_details": "Remote details",
    }
    try:
        missing_origin = await client.put(
            "/api/tutor/settings",
            headers={"X-CSRF-Token": csrf_token},
            json=valid_payload,
        )
        invalid_timezone = await client.put(
            "/api/tutor/settings",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
            },
            json={**valid_payload, "tutor_timezone": "Central Standard Time"},
        )
        fractional_price = await client.put(
            "/api/tutor/settings",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
            },
            json={**valid_payload, "session_price_cents": 82.5},
        )
        unchanged = await client.get("/api/tutor/settings")
        engine = create_engine(get_settings().database_url)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO accounts (id, email, role, display_name) "
                        "VALUES ('student-account', 'student@example.com', "
                        "'student', 'Student')"
                    )
                )
        finally:
            engine.dispose()
        student_token = issue_magic_link(
            get_settings().database_url, "student@example.com", 15 * 60
        )
        student_auth = await client.post(
            "/api/auth/magic-links/confirm", json={"token": student_token}
        )
        student_read = await client.get("/api/tutor/settings")
        student_write = await client.put(
            "/api/tutor/settings",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": student_auth.json()["csrf_token"],
            },
            json=valid_payload,
        )
        client.cookies.clear()
        anonymous = await client.get("/api/tutor/settings")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert missing_origin.status_code == 403
    assert invalid_timezone.status_code == 422
    assert fractional_price.status_code == 422
    assert unchanged.json()["session_price_cents"] == 7500
    assert unchanged.json()["tutor_timezone"] == "America/Chicago"
    assert student_read.status_code == 401
    assert student_write.status_code == 403
    assert anonymous.status_code == 401
