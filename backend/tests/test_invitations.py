from datetime import datetime, timedelta, timezone
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


async def authenticated_tutor_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[httpx.AsyncClient, str]:
    database_url = f"sqlite:///{tmp_path / 'invitations.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    monkeypatch.setenv(
        "TUTORING_INVITATION_ENCRYPTION_KEY",
        "a2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2s=",
    )
    get_settings.cache_clear()
    subprocess.run(
        [sys.executable, "-m", "app.bootstrap_tutor", "tutor@example.com"],
        cwd="backend",
        env={
            **os.environ,
            "TUTORING_ENVIRONMENT": "test",
            "TUTORING_DATABASE_URL": database_url,
        },
        check=True,
        capture_output=True,
    )

    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()),
        base_url="http://testserver",
    )
    await client.post("/api/auth/magic-links", json={"email": "tutor@example.com"})
    outbox = await client.get("/api/development/outbox")
    token = parse_qs(
        urlparse(outbox.json()["messages"][0]["magic_link"]).query
    )["token"][0]
    authenticated = await client.post(
        "/api/auth/magic-links/confirm", json={"token": token}
    )
    return client, authenticated.json()["csrf_token"]


@pytest.mark.anyio
async def test_tutor_creates_and_retrieves_one_active_manual_invitation_link(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={"email": " Known@Example.COM "},
        )
        retrieved = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}/link"
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert created.status_code == 201
    assert created.json().keys() == {
        "id",
        "email",
        "status",
        "invitation_url",
        "expires_at",
    }
    assert created.json()["email"] == "known@example.com"
    assert created.json()["status"] == "created"
    assert retrieved.status_code == 200
    assert retrieved.json() == {"invitation_url": created.json()["invitation_url"]}


@pytest.mark.anyio
async def test_tutor_creates_a_draft_invitation_for_a_known_invitee(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    try:
        response = await client.post(
            "/api/tutor/invitations",
            headers={"Origin": "http://testserver", "X-CSRF-Token": csrf_token},
            json={
                "email": "  Invitee@Example.COM ",
                "display_name": "Avery",
                "shared_personal_message": "I made this invitation for you.",
                "private_tutor_note": "Needs evening availability.",
            },
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "email": "invitee@example.com",
        "display_name": "Avery",
        "shared_personal_message": "I made this invitation for you.",
        "private_tutor_note": "Needs evening availability.",
        "status": "draft",
    }


@pytest.mark.anyio
async def test_anonymous_caller_cannot_create_an_invitation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'anonymous-invitation.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/api/tutor/invitations",
            headers={"Origin": "http://testserver", "X-CSRF-Token": "untrusted"},
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
    get_settings.cache_clear()

    assert response.status_code == 401
    assert response.json().keys() == {"code", "message", "request_id"}


@pytest.mark.anyio
async def test_invitation_creation_rejects_a_missing_origin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    try:
        response = await client.post(
            "/api/tutor/invitations",
            headers={"X-CSRF-Token": csrf_token},
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert response.status_code == 403


@pytest.mark.anyio
async def test_invitation_creation_rejects_a_missing_csrf_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, _ = await authenticated_tutor_client(monkeypatch, tmp_path)
    try:
        response = await client.post(
            "/api/tutor/invitations",
            headers={"Origin": "http://testserver"},
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert response.status_code == 403


@pytest.mark.anyio
async def test_invitation_creation_rejects_a_foreign_csrf_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, _ = await authenticated_tutor_client(monkeypatch, tmp_path)
    try:
        response = await client.post(
            "/api/tutor/invitations",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": "csrf-from-another-session",
            },
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert response.status_code == 403


@pytest.mark.anyio
async def test_student_caller_cannot_create_an_invitation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'student-invitation.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role) "
                    "VALUES ('student-account', 'student@example.com', 'student')"
                )
            )
    finally:
        engine.dispose()
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    get_settings.cache_clear()

    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()),
        base_url="http://testserver",
    )
    try:
        await client.post(
            "/api/auth/magic-links", json={"email": "student@example.com"}
        )
        outbox = await client.get("/api/development/outbox")
        token = parse_qs(
            urlparse(outbox.json()["messages"][0]["magic_link"]).query
        )["token"][0]
        authenticated = await client.post(
            "/api/auth/magic-links/confirm", json={"token": token}
        )
        response = await client.post(
            "/api/tutor/invitations",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": authenticated.json()["csrf_token"],
            },
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert response.status_code == 403


@pytest.mark.anyio
async def test_tutor_activates_an_invitation_with_a_seven_day_opaque_link(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
        activated = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/activate",
            headers=headers,
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert activated.status_code == 200
    assert activated.json().keys() == {
        "id",
        "status",
        "invitation_url",
        "expires_at",
    }
    assert activated.json()["id"] == created.json()["id"]
    assert activated.json()["status"] == "active"
    assert activated.json()["invitation_url"].startswith("/invite/")
    expires_at = datetime.fromisoformat(activated.json()["expires_at"])
    assert datetime.now(timezone.utc) + timedelta(days=6, hours=23) < expires_at
    assert expires_at < datetime.now(timezone.utc) + timedelta(days=7, minutes=1)


@pytest.mark.anyio
async def test_tutor_inspection_never_returns_the_raw_invitation_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Keep this Tutor-only.",
            },
        )
        activated = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/activate",
            headers=headers,
        )
        inspected = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}"
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert inspected.status_code == 200
    assert inspected.json().keys() == {
        "id",
        "email",
        "display_name",
        "shared_personal_message",
        "private_tutor_note",
        "status",
        "expires_at",
    }
    assert inspected.json()["status"] == "active"
    assert activated.json()["invitation_url"] not in inspected.text


@pytest.mark.anyio
async def test_activation_reveals_an_invitation_link_only_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
        invitation_id = created.json()["id"]
        first_activation = await client.post(
            f"/api/tutor/invitations/{invitation_id}/activate", headers=headers
        )
        second_activation = await client.post(
            f"/api/tutor/invitations/{invitation_id}/activate", headers=headers
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert first_activation.status_code == 200
    assert second_activation.status_code == 404
    assert "invitation_url" not in second_activation.text


@pytest.mark.anyio
async def test_anonymous_caller_cannot_inspect_a_tutor_invitation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
            },
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Never disclose this.",
            },
        )
        client.cookies.clear()
        inspected = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}"
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert inspected.status_code == 401
    assert "Never disclose this." not in inspected.text


@pytest.mark.anyio
async def test_student_caller_cannot_inspect_a_tutor_invitation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
            },
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Tutor-only context.",
            },
        )
        engine = create_engine(f"sqlite:///{tmp_path / 'invitations.sqlite3'}")
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO accounts (id, email, role) "
                        "VALUES ('student-account', 'student@example.com', 'student')"
                    )
                )
        finally:
            engine.dispose()
        await client.post(
            "/api/auth/magic-links", json={"email": "student@example.com"}
        )
        outbox = await client.get("/api/development/outbox")
        student_token = parse_qs(
            urlparse(outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        await client.post(
            "/api/auth/magic-links/confirm", json={"token": student_token}
        )
        inspected = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}"
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert inspected.status_code == 401
    assert "Tutor-only context." not in inspected.text


@pytest.mark.anyio
async def test_invitee_opens_an_active_invitation_with_only_allowlisted_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "I made this Invitation for you.",
                "private_tutor_note": "Never expose evening availability.",
            },
        )
        activated = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/activate",
            headers=headers,
        )
        client.cookies.clear()
        opened = await client.get(activated.json()["invitation_url"])
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert opened.status_code == 200
    assert opened.json() == {
        "email": "invitee@example.com",
        "display_name": "Avery",
        "shared_personal_message": "I made this Invitation for you.",
    }
    assert "Never expose evening availability." not in opened.text


@pytest.mark.anyio
async def test_tutor_corrects_the_bound_email_before_claim(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={
                "email": "typo@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
        activated = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/activate",
            headers=headers,
        )
        corrected = await client.patch(
            f"/api/tutor/invitations/{created.json()['id']}",
            headers=headers,
            json={"email": "  Corrected@Example.COM "},
        )
        opened = await client.get(activated.json()["invitation_url"])
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert corrected.status_code == 200
    assert corrected.json() == {
        "id": created.json()["id"],
        "email": "corrected@example.com",
        "status": "active",
    }
    assert opened.json()["email"] == "corrected@example.com"


@pytest.mark.anyio
async def test_tutor_revokes_an_active_invitation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
        activated = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/activate",
            headers=headers,
        )
        revoked = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/revoke",
            headers=headers,
        )
        reopened = await client.get(activated.json()["invitation_url"])
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert revoked.status_code == 200
    assert revoked.json() == {"id": created.json()["id"], "status": "revoked"}
    assert reopened.status_code == 404


@pytest.mark.anyio
async def test_regeneration_replaces_and_permanently_invalidates_the_prior_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
        activated = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/activate",
            headers=headers,
        )
        regenerated = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/regenerate",
            headers=headers,
        )
        prior_link = await client.get(activated.json()["invitation_url"])
        replacement_link = await client.get(regenerated.json()["invitation_url"])
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert regenerated.status_code == 200
    assert regenerated.json().keys() == {
        "id",
        "status",
        "invitation_url",
        "expires_at",
    }
    assert regenerated.json()["invitation_url"] != activated.json()["invitation_url"]
    assert prior_link.status_code == 404
    assert replacement_link.status_code == 200


@pytest.mark.anyio
async def test_opening_an_expired_link_records_the_terminal_expired_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TUTORING_INVITATION_TTL_SECONDS", "-1")
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Private.",
            },
        )
        activated = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/activate",
            headers=headers,
        )
        token = activated.json()["invitation_url"].rsplit("/", 1)[-1]
        opened = await client.get(f"/api/invitations/{token}")
        inspected = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}"
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert opened.status_code == 404
    assert inspected.status_code == 200
    assert inspected.json()["status"] == "expired"


@pytest.mark.anyio
async def test_unusable_invitation_tokens_have_indistinguishable_safe_responses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}

    async def activate(email: str) -> tuple[str, str]:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={
                "email": email,
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Never disclose this.",
            },
        )
        activated = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/activate",
            headers=headers,
        )
        return created.json()["id"], activated.json()["invitation_url"]

    try:
        revoked_id, revoked_url = await activate("revoked@example.com")
        await client.post(
            f"/api/tutor/invitations/{revoked_id}/revoke", headers=headers
        )

        superseded_id, superseded_url = await activate("superseded@example.com")
        await client.post(
            f"/api/tutor/invitations/{superseded_id}/regenerate", headers=headers
        )

        expired_id, expired_url = await activate("expired@example.com")
        claimed_id, claimed_url = await activate("claimed@example.com")
        engine = create_engine(f"sqlite:///{tmp_path / 'invitations.sqlite3'}")
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE invitations SET expires_at = :expires_at "
                        "WHERE id = :id"
                    ),
                    {"id": expired_id, "expires_at": "2000-01-01 00:00:00"},
                )
                connection.execute(
                    text("UPDATE invitations SET status = 'claimed' WHERE id = :id"),
                    {"id": claimed_id},
                )
        finally:
            engine.dispose()

        unusable_urls = [
            "/api/invitations/not-an-issued-token",
            revoked_url.replace("/invite/", "/api/invitations/"),
            superseded_url.replace("/invite/", "/api/invitations/"),
            expired_url.replace("/invite/", "/api/invitations/"),
            claimed_url.replace("/invite/", "/api/invitations/"),
        ]
        responses = [await client.get(url) for url in unusable_urls]
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert {
        (
            response.status_code,
            response.json()["code"],
            response.json()["message"],
            frozenset(response.json()),
        )
        for response in responses
    } == {
        (404, "not_found", "Resource not found", frozenset({"code", "message", "request_id"}))
    }
    assert all("Never disclose this." not in response.text for response in responses)
