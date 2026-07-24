from pathlib import Path
from urllib.parse import parse_qs, urlparse

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


async def authenticated_tutor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[httpx.AsyncClient, str]:
    database_url = f"sqlite:///{tmp_path / 'uncovered.sqlite3'}"
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
async def test_health_reports_ok(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv(
        "TUTORING_DATABASE_URL", f"sqlite:///{tmp_path / 'health.sqlite3'}"
    )
    get_settings.cache_clear()
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.get("/api/health")
    get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_role_session_rejects_anonymous_callers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv(
        "TUTORING_DATABASE_URL", f"sqlite:///{tmp_path / 'anonymous.sqlite3'}"
    )
    get_settings.cache_clear()
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.get("/api/auth/session")
    get_settings.cache_clear()

    assert response.status_code == 401


@pytest.mark.anyio
async def test_role_session_reports_the_active_role(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, _ = await authenticated_tutor(monkeypatch, tmp_path)
    try:
        response = await client.get("/api/auth/session")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"role": "tutor"}


@pytest.mark.anyio
async def test_testing_clock_overrides_now(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor(monkeypatch, tmp_path)
    try:
        response = await client.post(
            "/api/testing/clock",
            headers={"Origin": "http://testserver", "X-CSRF-Token": csrf_token},
            json={"now": "2026-08-01T12:00:00Z"},
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()["now"].startswith("2026-08-01T12:00:00")


@pytest.mark.anyio
async def test_invite_link_opens_the_invitation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor(monkeypatch, tmp_path)
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers={"Origin": "http://testserver", "X-CSRF-Token": csrf_token},
            json={"email": "invitee@example.com"},
        )
        opened = await client.get(created.json()["invitation_url"])
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert created.status_code == 201
    assert opened.status_code == 200
    assert opened.json()["email"] == "invitee@example.com"
