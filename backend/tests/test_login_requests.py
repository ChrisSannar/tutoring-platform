import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


async def authenticated_login_client(monkeypatch, tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'login-requests.sqlite3'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO accounts (id, email, role, display_name) VALUES "
                "('tutor', 'tutor@example.com', 'tutor', NULL), "
                "('student', 'student@example.com', 'student', 'Student')"
            )
        )
    engine.dispose()
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    get_settings.cache_clear()
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()),
        base_url="http://testserver",
        headers={"Origin": "http://127.0.0.1:7310"},
    )
    await client.post("/api/auth/magic-links", json={"email": "tutor@example.com"})
    outbox = await client.get("/api/development/outbox")
    token = parse_qs(urlparse(outbox.json()["messages"][-1]["magic_link"]).query)[
        "token"
    ][0]
    confirmed = await client.post(
        "/api/auth/magic-links/confirm", json={"token": token}
    )
    return client, confirmed.json()["csrf_token"], database_url


@pytest.mark.anyio
async def test_student_login_request_waits_for_tutor_generation(
    monkeypatch, tmp_path: Path
) -> None:
    client, csrf, _ = await authenticated_login_client(monkeypatch, tmp_path)
    try:
        before = await client.get("/api/development/outbox")
        accepted = await client.post(
            "/api/auth/magic-links", json={"email": "student@example.com"}
        )
        after = await client.get("/api/development/outbox")
        queue = await client.get("/api/tutor/login-requests")

        assert accepted.status_code == 202
        assert len(after.json()["messages"]) == len(before.json()["messages"])
        assert queue.status_code == 200
        assert queue.json()["login_requests"][0]["email"] == "student@example.com"

        request_id = queue.json()["login_requests"][0]["id"]
        generated = await client.post(
            f"/api/tutor/login-requests/{request_id}/magic-link",
            headers={"X-CSRF-Token": csrf},
        )
        assert generated.status_code == 201
        assert generated.json()["magic_link"].startswith("/sign-in/confirm?token=")

        token = parse_qs(urlparse(generated.json()["magic_link"]).query)["token"][0]
        inspected = await client.get(
            "/api/auth/magic-links/confirm", params={"token": token}
        )
        confirmed = await client.post(
            "/api/auth/magic-links/confirm", json={"token": token}
        )
        replay = await client.post(
            "/api/auth/magic-links/confirm", json={"token": token}
        )
        assert inspected.status_code == 200
        assert confirmed.status_code == 200
        assert confirmed.json()["role"] == "student"
        assert replay.status_code == 400

        await client.post("/api/auth/magic-links", json={"email": "tutor@example.com"})
        tutor_outbox = await client.get("/api/development/outbox")
        tutor_token = parse_qs(
            urlparse(tutor_outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        await client.post("/api/auth/magic-links/confirm", json={"token": tutor_token})
        assert (await client.get("/api/tutor/login-requests")).json()["login_requests"] == []
    finally:
        await client.aclose()
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_login_request_queue_and_mutations_are_tutor_only(
    monkeypatch, tmp_path: Path
) -> None:
    client, csrf, _ = await authenticated_login_client(monkeypatch, tmp_path)
    try:
        await client.post(
            "/api/auth/magic-links", json={"email": "student@example.com"}
        )
        request_id = (await client.get("/api/tutor/login-requests")).json()[
            "login_requests"
        ][0]["id"]
        generated = await client.post(
            f"/api/tutor/login-requests/{request_id}/magic-link",
            headers={"X-CSRF-Token": csrf},
        )
        token = parse_qs(urlparse(generated.json()["magic_link"]).query)["token"][0]
        await client.post("/api/auth/magic-links/confirm", json={"token": token})

        denied_queue = await client.get("/api/tutor/login-requests")
        denied_generation = await client.post(
            f"/api/tutor/login-requests/{request_id}/magic-link",
            headers={"X-CSRF-Token": csrf},
        )
        assert denied_queue.status_code == 401
        assert denied_generation.status_code == 403
    finally:
        await client.aclose()
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_dismissed_and_expired_login_requests_leave_active_queue(
    monkeypatch, tmp_path: Path
) -> None:
    client, csrf, database_url = await authenticated_login_client(monkeypatch, tmp_path)
    try:
        await client.post("/api/auth/magic-links", json={"email": "student@example.com"})
        request_id = (await client.get("/api/tutor/login-requests")).json()["login_requests"][0]["id"]
        generated = await client.post(
            f"/api/tutor/login-requests/{request_id}/magic-link",
            headers={"X-CSRF-Token": csrf},
        )
        dismissed_token = parse_qs(urlparse(generated.json()["magic_link"]).query)["token"][0]
        dismissed = await client.delete(
            f"/api/tutor/login-requests/{request_id}",
            headers={"X-CSRF-Token": csrf},
        )
        assert dismissed.status_code == 204
        assert (await client.get("/api/tutor/login-requests")).json()["login_requests"] == []
        assert (await client.post("/api/auth/magic-links/confirm", json={"token": dismissed_token})).status_code == 400

        await client.post("/api/auth/magic-links", json={"email": "student@example.com"})
        request_id = (await client.get("/api/tutor/login-requests")).json()["login_requests"][0]["id"]
        generated = await client.post(
            f"/api/tutor/login-requests/{request_id}/magic-link",
            headers={"X-CSRF-Token": csrf},
        )
        engine = create_engine(database_url)
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE magic_link_tokens SET expires_at = '2000-01-01' WHERE token_hash IS NOT NULL")
            )
        engine.dispose()
        assert generated.status_code == 201
        assert (await client.get("/api/tutor/login-requests")).json()["login_requests"] == []
    finally:
        await client.aclose()
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_repository_command_emits_one_tutor_login_link(
    monkeypatch, tmp_path: Path
) -> None:
    client, _, database_url = await authenticated_login_client(monkeypatch, tmp_path)
    await client.aclose()
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }
    result = subprocess.run(
        [sys.executable, "-m", "app.generate_tutor_login_link"],
        cwd="backend",
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    get_settings.cache_clear()

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.strip().startswith("/sign-in/confirm?token=")
