from concurrent.futures import ThreadPoolExecutor
import asyncio
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
    linked: bool = False,
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
    if linked:
        await client.post(
            "/api/inquiries",
            json={"email": email, "message": "Please consider tutoring me."},
        )
        inquiries = await client.get("/api/tutor/inquiries")
        created = await client.post(
            f"/api/tutor/inquiries/{inquiries.json()['inquiries'][0]['id']}/invitation",
            headers=headers,
        )
    else:
        created = await client.post(
            "/api/tutor/invitations", headers=headers, json={"email": email}
        )
    client.cookies.clear()
    return client, created.json()["invitation_url"].removeprefix("/invite/")


@pytest.mark.anyio
async def test_original_invitation_link_claims_a_student_session_and_promotion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, invitation_token = await active_invitation(monkeypatch, tmp_path)
    try:
        opened = await client.get(f"/api/invitations/{invitation_token}")
        claimed = await client.post(
            f"/api/invitations/{invitation_token}/claim",
            json={"display_name": "Avery Chen"},
        )
        reopened = await client.get(f"/api/invitations/{invitation_token}")
        student_session = await client.get("/api/student/session")
        funding = await client.get("/api/student/funding")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert opened.json()["email"] == "invitee@example.com"
    assert claimed.status_code == 200
    assert claimed.json() == {
        "status": "claimed",
        "role": "student",
        "email": "invitee@example.com",
        "display_name": "Avery Chen",
        "csrf_token": claimed.json()["csrf_token"],
    }
    assert claimed.cookies["tutoring_session"]
    assert reopened.status_code == 404
    assert student_session.status_code == 200
    assert funding.json() == {
        "first_session_promotion": "available",
        "session_credits": 0,
    }


@pytest.mark.anyio
async def test_one_step_claim_requires_a_non_empty_display_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, invitation_token = await active_invitation(monkeypatch, tmp_path)
    try:
        rejected = await client.post(
            f"/api/invitations/{invitation_token}/claim",
            json={"display_name": "   "},
        )
        accepted = await client.post(
            f"/api/invitations/{invitation_token}/claim",
            json={"display_name": "Avery"},
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert rejected.status_code == 422
    assert accepted.status_code == 200


@pytest.mark.anyio
async def test_claimed_invitee_moves_from_the_inquiry_queue_to_the_student_list(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, invitation_token = await active_invitation(monkeypatch, tmp_path, linked=True)
    try:
        await client.get(f"/api/invitations/{invitation_token}")
        await client.post(
            f"/api/invitations/{invitation_token}/claim",
            json={"display_name": "Avery Chen"},
        )
        await client.post(
            "/api/auth/magic-links", json={"email": "tutor@example.com"}
        )
        outbox = await client.get("/api/development/outbox")
        tutor_token = parse_qs(
            urlparse(outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        await client.post(
            "/api/auth/magic-links/confirm", json={"token": tutor_token}
        )
        inquiries = await client.get("/api/tutor/inquiries")
        students = await client.get("/api/tutor/students")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert inquiries.json() == {"inquiries": []}
    assert students.json() == {
        "students": [
            {
                "id": students.json()["students"][0]["id"],
                "email": "invitee@example.com",
                "display_name": "Avery Chen",
            }
        ]
    }


@pytest.mark.anyio
async def test_concurrent_original_link_claims_have_exactly_one_winner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    setup_client, invitation_token = await active_invitation(monkeypatch, tmp_path)
    await setup_client.aclose()
    application = create_app()
    first = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application), base_url="http://testserver"
    )
    second = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application), base_url="http://testserver"
    )
    try:
        responses = await asyncio.gather(
            first.post(
                f"/api/invitations/{invitation_token}/claim",
                json={"display_name": "Avery One"},
            ),
            second.post(
                f"/api/invitations/{invitation_token}/claim",
                json={"display_name": "Avery Two"},
            ),
        )
        winner = first if responses[0].status_code == 200 else second
        funding = await winner.get("/api/student/funding")
    finally:
        await first.aclose()
        await second.aclose()
        get_settings.cache_clear()

    assert sorted(response.status_code for response in responses) == [200, 409]
    assert funding.json() == {
        "first_session_promotion": "available",
        "session_credits": 0,
    }


@pytest.mark.anyio
async def test_retired_invitation_claim_ceremony_is_not_reachable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, invitation_token = await active_invitation(monkeypatch, tmp_path)
    try:
        second_link = await client.post(
            f"/api/invitations/{invitation_token}/magic-links",
            json={"email": "invitee@example.com"},
        )
        second_link_inspection = await client.get(
            "/api/invitation-claims/confirm", params={"token": "retired-token"}
        )
        second_link_consumption = await client.post(
            "/api/invitation-claims/confirm",
            json={"token": "retired-token", "display_name": "Avery"},
        )
        draft_activation = await client.post(
            "/api/tutor/invitations/retired-draft/activate"
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert {
        second_link.status_code,
        second_link_inspection.status_code,
        second_link_consumption.status_code,
        draft_activation.status_code,
    } == {404}


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
        claimed = await client.post(
            f"/api/invitations/{invitation_token}/claim",
            json={"display_name": "Avery"},
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
            json={"email": "invitee@example.com"},
        )
        second_invitation_token = second.json()["invitation_url"].removeprefix(
            "/invite/"
        )
        client.cookies.clear()
        first_claim = await client.post(
            f"/api/invitations/{first_invitation_token}/claim",
            json={"display_name": "Avery"},
        )
        client.cookies.clear()
        second_claim = await client.post(
            f"/api/invitations/{second_invitation_token}/claim",
            json={"display_name": "Avery Two"},
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
                f"{base_url}/api/invitations/{invitation_token}/claim",
                json={"display_name": display_name},
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
