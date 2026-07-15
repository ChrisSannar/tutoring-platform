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


async def active_invitation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    email: str = "invitee@example.com",
) -> tuple[httpx.AsyncClient, str]:
    database_url = f"sqlite:///{tmp_path / 'invitation-claim.sqlite3'}"
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
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()),
        base_url="http://testserver",
    )
    await client.post("/api/auth/magic-links", json={"email": "tutor@example.com"})
    outbox = await client.get("/api/development/outbox")
    tutor_token = parse_qs(
        urlparse(outbox.json()["messages"][-1]["magic_link"]).query
    )["token"][0]
    authenticated = await client.post(
        "/api/auth/magic-links/confirm", json={"token": tutor_token}
    )
    headers = {
        "Origin": "http://testserver",
        "X-CSRF-Token": authenticated.json()["csrf_token"],
    }
    created = await client.post(
        "/api/tutor/invitations",
        headers=headers,
        json={
            "email": email,
            "display_name": "Avery",
            "shared_personal_message": "Welcome.",
            "private_tutor_note": "Tutor-only.",
        },
    )
    activated = await client.post(
        f"/api/tutor/invitations/{created.json()['id']}/activate",
        headers=headers,
    )
    client.cookies.clear()
    return client, activated.json()["invitation_url"].removeprefix("/invite/")


@pytest.mark.anyio
async def test_invitee_requests_verification_for_the_bound_email(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, invitation_token = await active_invitation(monkeypatch, tmp_path)
    try:
        requested = await client.post(
            f"/api/invitations/{invitation_token}/magic-links",
            json={"email": " Invitee@Example.COM "},
        )
        outbox = await client.get("/api/development/outbox")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert requested.status_code == 202
    assert requested.json() == {
        "status": "accepted",
        "message": "If the address matches, a verification link has been sent.",
    }
    verification = outbox.json()["messages"][-1]
    assert verification["to"] == "invitee@example.com"
    assert verification["magic_link"].startswith(
        "/student/claim/confirm?token="
    )


@pytest.mark.anyio
async def test_invitation_verification_link_requires_confirmation_before_claim(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, invitation_token = await active_invitation(monkeypatch, tmp_path)
    try:
        await client.post(
            f"/api/invitations/{invitation_token}/magic-links",
            json={"email": "invitee@example.com"},
        )
        outbox = await client.get("/api/development/outbox")
        claim_token = parse_qs(
            urlparse(outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        confirmation = await client.get(
            "/api/invitation-claims/confirm", params={"token": claim_token}
        )
        invitation_still_active = await client.get(
            f"/api/invitations/{invitation_token}"
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert confirmation.status_code == 200
    assert confirmation.json() == {
        "status": "confirmation_required",
        "email": "invitee@example.com",
        "display_name": "Avery",
    }
    assert invitation_still_active.status_code == 200


@pytest.mark.anyio
async def test_verified_invitee_claims_with_an_edited_display_name_and_bound_email(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, invitation_token = await active_invitation(monkeypatch, tmp_path)
    try:
        await client.post(
            f"/api/invitations/{invitation_token}/magic-links",
            json={"email": "invitee@example.com"},
        )
        outbox = await client.get("/api/development/outbox")
        claim_token = parse_qs(
            urlparse(outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        claimed = await client.post(
            "/api/invitation-claims/confirm",
            json={"token": claim_token, "display_name": "Avery Chen"},
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert claimed.status_code == 200
    assert claimed.json() == {
        "status": "claimed",
        "role": "student",
        "email": "invitee@example.com",
        "display_name": "Avery Chen",
        "csrf_token": claimed.json()["csrf_token"],
    }
