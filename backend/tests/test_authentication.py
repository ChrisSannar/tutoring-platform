import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

from alembic import command
from alembic.config import Config
import httpx
import pytest

from app.config import get_settings
from app.main import create_app


def test_repository_command_bootstraps_exactly_one_tutor(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'authentication.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }

    first = subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "Tutor@Example.com"],
        cwd="backend",
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    second = subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "other@example.com"],
        cwd="backend",
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert first.returncode == 0
    assert first.stdout.strip() == "Tutor created for tutor@example.com"
    assert second.returncode == 1
    assert second.stderr.strip() == "A Tutor already exists"


@pytest.mark.anyio
async def test_magic_link_requests_do_not_reveal_whether_an_account_exists(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'enumeration.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "tutor@example.com"],
        cwd="backend",
        env=environment,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        known = await client.post(
            "/api/auth/magic-links", json={"email": " Tutor@Example.com "}
        )
        unknown = await client.post(
            "/api/auth/magic-links", json={"email": "unknown@example.com"}
        )
    get_settings.cache_clear()

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json() == {
        "status": "accepted",
        "message": "If the address is eligible, a sign-in link has been sent.",
    }


@pytest.mark.anyio
async def test_eligible_tutor_receives_a_magic_link_in_the_development_outbox(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'outbox.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "tutor@example.com"],
        cwd="backend",
        env=environment,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/auth/magic-links", json={"email": "tutor@example.com"}
        )
        outbox = await client.get("/api/development/outbox")
    get_settings.cache_clear()

    assert outbox.status_code == 200
    messages = outbox.json()["messages"]
    assert len(messages) == 1
    assert messages[0]["to"] == "tutor@example.com"
    assert messages[0]["magic_link"].startswith("/tutor/sign-in/confirm?token=")


@pytest.mark.anyio
async def test_opening_a_magic_link_requires_confirmation_without_consuming_it(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'confirmation.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "tutor@example.com"],
        cwd="backend",
        env=environment,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/auth/magic-links", json={"email": "tutor@example.com"}
        )
        outbox = await client.get("/api/development/outbox")
        magic_link = outbox.json()["messages"][0]["magic_link"]
        token = parse_qs(urlparse(magic_link).query)["token"][0]
        first_open = await client.get(
            "/api/auth/magic-links/confirm", params={"token": token}
        )
        second_open = await client.get(
            "/api/auth/magic-links/confirm", params={"token": token}
        )
    get_settings.cache_clear()

    assert first_open.status_code == second_open.status_code == 200
    assert first_open.json() == second_open.json() == {
        "status": "confirmation_required"
    }
    assert "tutoring_session" not in first_open.cookies


@pytest.mark.anyio
async def test_confirming_a_magic_link_once_creates_a_secure_tutor_session(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'session.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "tutor@example.com"],
        cwd="backend",
        env=environment,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/auth/magic-links", json={"email": "tutor@example.com"}
        )
        outbox = await client.get("/api/development/outbox")
        magic_link = outbox.json()["messages"][0]["magic_link"]
        token = parse_qs(urlparse(magic_link).query)["token"][0]
        confirmed = await client.post(
            "/api/auth/magic-links/confirm", json={"token": token}
        )
        replayed = await client.post(
            "/api/auth/magic-links/confirm", json={"token": token}
        )
    get_settings.cache_clear()

    assert confirmed.status_code == 200
    assert confirmed.json().keys() == {"status", "role", "csrf_token"}
    assert confirmed.json()["status"] == "authenticated"
    assert confirmed.json()["role"] == "tutor"
    set_cookie = confirmed.headers["set-cookie"]
    assert "tutoring_session=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/" in set_cookie
    assert "Domain=" not in set_cookie
    assert replayed.status_code == 400


@pytest.mark.anyio
async def test_magic_link_requests_are_limited_to_five_per_email_per_hour(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'email-limit.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        responses = [
            await client.post(
                "/api/auth/magic-links", json={"email": "same@example.com"}
            )
            for _ in range(6)
        ]
    get_settings.cache_clear()

    assert [response.status_code for response in responses] == [
        202,
        202,
        202,
        202,
        202,
        429,
    ]


@pytest.mark.anyio
async def test_magic_link_requests_are_limited_to_twenty_per_ip_per_hour(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'ip-limit.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        responses = [
            await client.post(
                "/api/auth/magic-links", json={"email": f"person-{index}@example.com"}
            )
            for index in range(21)
        ]
    get_settings.cache_clear()

    assert [response.status_code for response in responses] == [202] * 20 + [429]


@pytest.mark.anyio
async def test_magic_link_expires_after_its_configured_fifteen_minute_window(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'expired-link.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "tutor@example.com"],
        cwd="backend",
        env=environment,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_MAGIC_LINK_TTL_SECONDS", "0")
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/auth/magic-links", json={"email": "tutor@example.com"}
        )
        outbox = await client.get("/api/development/outbox")
        magic_link = outbox.json()["messages"][0]["magic_link"]
        token = parse_qs(urlparse(magic_link).query)["token"][0]
        expired = await client.post(
            "/api/auth/magic-links/confirm", json={"token": token}
        )
    get_settings.cache_clear()

    assert expired.status_code == 400
    assert expired.json().keys() == {"code", "message", "request_id"}


@pytest.mark.anyio
async def test_logout_requires_same_origin_and_csrf_then_revokes_the_session(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'logout.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "tutor@example.com"],
        cwd="backend",
        env=environment,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/auth/magic-links", json={"email": "tutor@example.com"}
        )
        outbox = await client.get("/api/development/outbox")
        token = parse_qs(
            urlparse(outbox.json()["messages"][0]["magic_link"]).query
        )["token"][0]
        authenticated = await client.post(
            "/api/auth/magic-links/confirm", json={"token": token}
        )
        csrf_token = authenticated.json()["csrf_token"]
        missing_origin = await client.post(
            "/api/auth/logout", headers={"X-CSRF-Token": csrf_token}
        )
        foreign_origin = await client.post(
            "/api/auth/logout",
            headers={
                "Origin": "https://attacker.example",
                "X-CSRF-Token": csrf_token,
            },
        )
        missing_csrf = await client.post(
            "/api/auth/logout", headers={"Origin": "http://testserver"}
        )
        logged_out = await client.post(
            "/api/auth/logout",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
            },
        )
        after_logout = await client.get("/api/tutor/session")
    get_settings.cache_clear()

    assert missing_origin.status_code == 403
    assert foreign_origin.status_code == 403
    assert missing_csrf.status_code == 403
    assert logged_out.status_code == 204
    assert after_logout.status_code == 401


@pytest.mark.anyio
async def test_tutor_session_expires_after_the_inactivity_limit(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'inactive-session.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "tutor@example.com"],
        cwd="backend",
        env=environment,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_SESSION_INACTIVITY_SECONDS", "0")
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/auth/magic-links", json={"email": "tutor@example.com"}
        )
        outbox = await client.get("/api/development/outbox")
        token = parse_qs(
            urlparse(outbox.json()["messages"][0]["magic_link"]).query
        )["token"][0]
        await client.post("/api/auth/magic-links/confirm", json={"token": token})
        session = await client.get("/api/tutor/session")
    get_settings.cache_clear()

    assert session.status_code == 401


@pytest.mark.anyio
async def test_tutor_session_never_survives_its_absolute_limit(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'absolute-session.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "tutor@example.com"],
        cwd="backend",
        env=environment,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_SESSION_ABSOLUTE_SECONDS", "0")
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/auth/magic-links", json={"email": "tutor@example.com"}
        )
        outbox = await client.get("/api/development/outbox")
        token = parse_qs(
            urlparse(outbox.json()["messages"][0]["magic_link"]).query
        )["token"][0]
        await client.post("/api/auth/magic-links/confirm", json={"token": token})
        session = await client.get("/api/tutor/session")
    get_settings.cache_clear()

    assert session.status_code == 401


@pytest.mark.anyio
async def test_authentication_rotates_and_revokes_the_previous_session(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'rotation.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    environment = {
        **os.environ,
        "TUTORING_ENVIRONMENT": "test",
        "TUTORING_DATABASE_URL": database_url,
    }
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "tutor@example.com"],
        cwd="backend",
        env=environment,
        check=True,
        capture_output=True,
    )
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    get_settings.cache_clear()

    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/auth/magic-links", json={"email": "tutor@example.com"}
        )
        first_outbox = await client.get("/api/development/outbox")
        first_token = parse_qs(
            urlparse(first_outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        first_auth = await client.post(
            "/api/auth/magic-links/confirm", json={"token": first_token}
        )
        old_session = first_auth.cookies["tutoring_session"]

        await client.post(
            "/api/auth/magic-links", json={"email": "tutor@example.com"}
        )
        second_outbox = await client.get("/api/development/outbox")
        second_token = parse_qs(
            urlparse(second_outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        second_auth = await client.post(
            "/api/auth/magic-links/confirm", json={"token": second_token}
        )

    old_transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=old_transport,
        base_url="http://testserver",
        cookies={"tutoring_session": old_session},
    ) as old_client:
        old_session_response = await old_client.get("/api/tutor/session")
    get_settings.cache_clear()

    assert second_auth.cookies["tutoring_session"] != old_session
    assert old_session_response.status_code == 401
