from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
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
        transport=httpx.ASGITransport(app=create_app(), raise_app_exceptions=False),
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


@pytest.mark.anyio
async def test_successful_claim_continues_through_a_student_session(
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
            json={"token": claim_token, "display_name": "Avery"},
        )
        student_session = await client.get("/api/student/session")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert claimed.cookies["tutoring_session"]
    assert student_session.status_code == 200
    assert student_session.json() == {
        "role": "student",
        "email": "invitee@example.com",
        "display_name": "Avery",
    }


@pytest.mark.anyio
async def test_invitation_claim_rotates_the_existing_browser_session(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, invitation_token = await active_invitation(monkeypatch, tmp_path)
    try:
        await client.post("/api/auth/magic-links", json={"email": "tutor@example.com"})
        outbox = await client.get("/api/development/outbox")
        tutor_token = parse_qs(
            urlparse(outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        await client.post("/api/auth/magic-links/confirm", json={"token": tutor_token})
        prior_session = client.cookies["tutoring_session"]
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
            json={"token": claim_token, "display_name": "Avery"},
        )
        old_browser = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=create_app()),
            base_url="http://testserver",
            cookies={"tutoring_session": prior_session},
        )
        try:
            prior_session_result = await old_browser.get("/api/tutor/session")
        finally:
            await old_browser.aclose()
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert claimed.status_code == 200
    assert claimed.cookies["tutoring_session"] != prior_session
    assert prior_session_result.status_code == 401


@pytest.mark.anyio
async def test_one_email_cannot_be_associated_with_multiple_student_accounts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, first_invitation_token = await active_invitation(monkeypatch, tmp_path)
    try:
        await client.post("/api/auth/magic-links", json={"email": "tutor@example.com"})
        outbox = await client.get("/api/development/outbox")
        tutor_token = parse_qs(
            urlparse(outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        tutor = await client.post(
            "/api/auth/magic-links/confirm", json={"token": tutor_token}
        )
        headers = {
            "Origin": "http://testserver",
            "X-CSRF-Token": tutor.json()["csrf_token"],
        }
        second = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome again.",
                "private_tutor_note": "Tutor-only.",
            },
        )
        activated_second = await client.post(
            f"/api/tutor/invitations/{second.json()['id']}/activate",
            headers=headers,
        )
        second_invitation_token = activated_second.json()[
            "invitation_url"
        ].removeprefix("/invite/")
        client.cookies.clear()
        await client.post(
            f"/api/invitations/{first_invitation_token}/magic-links",
            json={"email": "invitee@example.com"},
        )
        outbox = await client.get("/api/development/outbox")
        first_claim_token = parse_qs(
            urlparse(outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        await client.post(
            f"/api/invitations/{second_invitation_token}/magic-links",
            json={"email": "invitee@example.com"},
        )
        outbox = await client.get("/api/development/outbox")
        second_claim_token = parse_qs(
            urlparse(outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        first_claim = await client.post(
            "/api/invitation-claims/confirm",
            json={"token": first_claim_token, "display_name": "Avery"},
        )
        client.cookies.clear()
        second_claim = await client.post(
            "/api/invitation-claims/confirm",
            json={"token": second_claim_token, "display_name": "Avery Two"},
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert first_claim.status_code == 200
    assert second_claim.status_code == 409
    assert second_claim.json().keys() == {"code", "message", "request_id"}


@pytest.mark.anyio
async def test_concurrent_invitation_claim_attempts_have_one_winner(
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
    finally:
        await client.aclose()

    with socket.socket() as available_port:
        available_port.bind(("127.0.0.1", 0))
        port = available_port.getsockname()[1]
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--workers",
            "2",
            "--no-access-log",
        ],
        cwd="backend",
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                if httpx.get(f"{base_url}/api/health").status_code == 200:
                    break
            except httpx.ConnectError:
                time.sleep(0.05)
        else:
            raise AssertionError("live HTTP test server did not start")

        barrier = threading.Barrier(2)

        def submit_claim(display_name: str) -> httpx.Response:
            barrier.wait()
            return httpx.post(
                f"{base_url}/api/invitation-claims/confirm",
                json={"token": claim_token, "display_name": display_name},
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(submit_claim, "Avery One"),
                executor.submit(submit_claim, "Avery Two"),
            ]
            responses = [future.result(timeout=10) for future in futures]
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
        get_settings.cache_clear()

    assert sorted(response.status_code for response in responses) == [200, 409]
