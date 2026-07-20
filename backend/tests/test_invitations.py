import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, urlparse

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.authentication import issue_magic_link
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
        client.cookies.clear()
        anonymous_retrieval = await client.get(
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
    assert anonymous_retrieval.status_code == 401
    assert created.json()["invitation_url"] not in anonymous_retrieval.text


@pytest.mark.anyio
async def test_tutor_cannot_create_a_superseded_draft_invitation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    try:
        response = await client.post(
            "/api/tutor/invitations",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
            },
            json={
                "email": "invitee@example.com",
                "display_name": "Avery",
                "shared_personal_message": "Welcome.",
                "private_tutor_note": "Tutor-only.",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 422


@pytest.mark.anyio
async def test_tutor_creates_an_invitation_from_an_inquiry_in_one_action(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        await client.post(
            "/api/inquiries",
            json={
                "email": "inquiry-prospect@example.com",
                "message": "I would like tutoring support.",
            },
        )
        listed = await client.get("/api/tutor/inquiries")
        inquiry_id = listed.json()["inquiries"][0]["id"]
        created = await client.post(
            f"/api/tutor/inquiries/{inquiry_id}/invitation", headers=headers
        )
        relisted = await client.get("/api/tutor/inquiries")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert created.status_code == 201
    assert created.json()["email"] == "inquiry-prospect@example.com"
    assert created.json()["status"] == "created"
    assert created.json()["invitation_url"].startswith("/invite/")
    assert relisted.json()["inquiries"][0]["status"] == "invited"
    assert relisted.json()["inquiries"][0]["invitation_id"] == created.json()["id"]


@pytest.mark.anyio
async def test_revocation_erases_a_retrievable_invitation_link(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={"email": "revoked-direct@example.com"},
        )
        invitation_id = created.json()["id"]
        revoked = await client.post(
            f"/api/tutor/invitations/{invitation_id}/revoke", headers=headers
        )
        retrieved = await client.get(
            f"/api/tutor/invitations/{invitation_id}/link"
        )
        opened = await client.get(created.json()["invitation_url"])
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert revoked.status_code == 200
    assert revoked.json() == {"id": invitation_id, "status": "revoked"}
    assert retrieved.status_code == 404
    assert opened.status_code == 404


@pytest.mark.anyio
async def test_regeneration_replaces_the_retrievable_link_and_invalidates_the_prior_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={"email": "regenerate-direct@example.com"},
        )
        invitation_id = created.json()["id"]
        regenerated = await client.post(
            f"/api/tutor/invitations/{invitation_id}/regenerate", headers=headers
        )
        retrieved = await client.get(
            f"/api/tutor/invitations/{invitation_id}/link"
        )
        prior_open = await client.get(created.json()["invitation_url"])
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert regenerated.status_code == 200
    assert regenerated.json()["status"] == "created"
    assert regenerated.json()["invitation_url"] != created.json()["invitation_url"]
    assert retrieved.json() == {
        "invitation_url": regenerated.json()["invitation_url"]
    }
    assert prior_open.status_code == 404


@pytest.mark.anyio
async def test_opening_a_created_invitation_is_observational_and_keeps_it_retrievable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={"email": "scanner-safe@example.com"},
        )
        opened = await client.get(created.json()["invitation_url"])
        retrieved = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}/link"
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert opened.status_code == 200
    assert opened.json()["email"] == "scanner-safe@example.com"
    assert retrieved.json() == {"invitation_url": created.json()["invitation_url"]}


@pytest.mark.anyio
async def test_invitation_http_lifecycle_records_evidence_and_preserves_terminal_revocation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={"email": "lifecycle@example.com"},
        )
        invitation_id = created.json()["id"]
        before_open = await client.get(f"/api/tutor/invitations/{invitation_id}")
        opened = await client.get(created.json()["invitation_url"])
        after_open = await client.get(f"/api/tutor/invitations/{invitation_id}")
        opened_again = await client.get(created.json()["invitation_url"])
        after_second_open = await client.get(
            f"/api/tutor/invitations/{invitation_id}"
        )
        revoked = await client.post(
            f"/api/tutor/invitations/{invitation_id}/revoke", headers=headers
        )
        revoked_again = await client.post(
            f"/api/tutor/invitations/{invitation_id}/revoke", headers=headers
        )
        after_revoke = await client.get(f"/api/tutor/invitations/{invitation_id}")
        terminal_regeneration = await client.post(
            f"/api/tutor/invitations/{invitation_id}/regenerate", headers=headers
        )
        terminal_open = await client.get(created.json()["invitation_url"])
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert before_open.json()["status"] == "created"
    assert before_open.json()["created_at"] is not None
    assert before_open.json()["first_opened_at"] is None
    assert opened.status_code == opened_again.status_code == 200
    assert after_open.json()["status"] == "opened"
    assert after_open.json()["expires_at"] == before_open.json()["expires_at"]
    assert after_open.json()["first_opened_at"] is not None
    assert (
        after_second_open.json()["first_opened_at"]
        == after_open.json()["first_opened_at"]
    )
    assert revoked.json() == revoked_again.json() == {
        "id": invitation_id,
        "status": "revoked",
    }
    assert after_revoke.json()["status"] == "revoked"
    assert after_revoke.json()["revoked_at"] is not None
    assert after_revoke.json()["claimed_at"] is None
    assert after_revoke.json()["expired_at"] is None
    assert terminal_regeneration.status_code == 409
    assert terminal_open.status_code == 404


@pytest.mark.anyio
async def test_claimed_invitation_exposes_atomic_claim_evidence_to_the_tutor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={"email": "claimed-evidence@example.com"},
        )
        token = created.json()["invitation_url"].rsplit("/", 1)[-1]
        claimed = await client.post(
            f"/api/invitations/{token}/claim", json={"display_name": "Avery"}
        )
        await client.post("/api/auth/magic-links", json={"email": "tutor@example.com"})
        outbox = await client.get("/api/development/outbox")
        tutor_token = parse_qs(
            urlparse(outbox.json()["messages"][-1]["magic_link"]).query
        )["token"][0]
        tutor = await client.post(
            "/api/auth/magic-links/confirm", json={"token": tutor_token}
        )
        inspected = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}"
        )
        terminal_revoke = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/revoke",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": tutor.json()["csrf_token"],
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert claimed.status_code == 200
    assert inspected.json()["status"] == "claimed"
    assert inspected.json()["claimed_at"] is not None
    assert inspected.json()["expired_at"] is None
    assert inspected.json()["revoked_at"] is None
    assert terminal_revoke.status_code == 409


@pytest.mark.anyio
async def test_live_claim_and_revocation_race_has_one_evidence_backed_terminal_winner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    setup_client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    created = await setup_client.post(
        "/api/tutor/invitations",
        headers=headers,
        json={"email": "racing-lifecycle@example.com"},
    )
    invitation_id = created.json()["id"]
    token = created.json()["invitation_url"].rsplit("/", 1)[-1]
    tutor_cookies = dict(setup_client.cookies)
    await setup_client.aclose()

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

        def claim() -> httpx.Response:
            barrier.wait()
            return httpx.post(
                f"{base_url}/api/invitations/{token}/claim",
                json={"display_name": "Race Winner"},
            )

        def revoke() -> httpx.Response:
            barrier.wait()
            return httpx.post(
                f"{base_url}/api/tutor/invitations/{invitation_id}/revoke",
                headers=headers,
                cookies=tutor_cookies,
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            claim_future = executor.submit(claim)
            revoke_future = executor.submit(revoke)
            claim_response = claim_future.result(timeout=10)
            revoke_response = revoke_future.result(timeout=10)
        inspected = httpx.get(
            f"{base_url}/api/tutor/invitations/{invitation_id}",
            cookies=tutor_cookies,
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
        get_settings.cache_clear()

    assert sorted([claim_response.status_code, revoke_response.status_code]) == [200, 409]
    assert inspected.status_code == 200
    record = inspected.json()
    if claim_response.status_code == 200:
        assert record["status"] == "claimed"
        assert record["claimed_at"] is not None
        assert record["revoked_at"] is None
    else:
        assert record["status"] == "revoked"
        assert record["revoked_at"] is not None
        assert record["claimed_at"] is None


@pytest.mark.anyio
async def test_expiration_erases_the_retrievable_invitation_link_lazily(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TUTORING_INVITATION_TTL_SECONDS", "-1")
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    try:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={"email": "expired-direct@example.com"},
        )
        retrieved = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}/link"
        )
        inspected = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}"
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert retrieved.status_code == 404
    assert inspected.json()["status"] == "expired"
    assert inspected.json()["expired_at"] is not None


@pytest.mark.anyio
async def test_every_expired_invitation_interaction_persists_the_same_terminal_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TUTORING_INVITATION_TTL_SECONDS", "-1")
    client, csrf_token = await authenticated_tutor_client(monkeypatch, tmp_path)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}

    async def create(email: str) -> dict:
        response = await client.post(
            "/api/tutor/invitations", headers=headers, json={"email": email}
        )
        return response.json()

    try:
        opening = await create("expire-open@example.com")
        claiming = await create("expire-claim@example.com")
        correction = await create("expire-correct@example.com")
        regeneration = await create("expire-regenerate@example.com")
        revocation = await create("expire-revoke@example.com")
        inspection = await create("expire-inspect@example.com")

        results = {
            opening["id"]: await client.get(opening["invitation_url"]),
            claiming["id"]: await client.post(
                f"/api/invitations/{claiming['invitation_url'].rsplit('/', 1)[-1]}/claim",
                json={"display_name": "Late"},
            ),
            correction["id"]: await client.patch(
                f"/api/tutor/invitations/{correction['id']}",
                headers=headers,
                json={"email": "corrected@example.com"},
            ),
            regeneration["id"]: await client.post(
                f"/api/tutor/invitations/{regeneration['id']}/regenerate",
                headers=headers,
            ),
            revocation["id"]: await client.post(
                f"/api/tutor/invitations/{revocation['id']}/revoke", headers=headers
            ),
            inspection["id"]: await client.get(
                f"/api/tutor/invitations/{inspection['id']}"
            ),
        }
        records = {
            invitation_id: await client.get(
                f"/api/tutor/invitations/{invitation_id}"
            )
            for invitation_id in results
        }
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert results[opening["id"]].status_code == 404
    assert results[claiming["id"]].status_code == 409
    assert results[correction["id"]].status_code == 409
    assert results[regeneration["id"]].status_code == 409
    assert results[revocation["id"]].status_code == 409
    assert results[inspection["id"]].status_code == 200
    assert all(record.json()["status"] == "expired" for record in records.values())
    assert all(record.json()["expired_at"] is not None for record in records.values())


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
            json={"email": "invitee@example.com"},
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
            json={"email": "invitee@example.com"},
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
            json={"email": "invitee@example.com"},
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
            json={"email": "invitee@example.com"},
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
        token = issue_magic_link(database_url, "student@example.com", 15 * 60)
        authenticated = await client.post(
            "/api/auth/magic-links/confirm", json={"token": token}
        )
        response = await client.post(
            "/api/tutor/invitations",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": authenticated.json()["csrf_token"],
            },
            json={"email": "invitee@example.com"},
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert response.status_code == 403


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
            json={"email": "invitee@example.com"},
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
        "created_at",
        "first_opened_at",
        "claimed_at",
        "expired_at",
        "revoked_at",
        "expires_at",
    }
    assert inspected.json()["status"] == "created"
    assert created.json()["invitation_url"] not in inspected.text


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
            json={"email": "invitee@example.com"},
        )
        client.cookies.clear()
        inspected = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}"
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert inspected.status_code == 401
    assert created.json()["invitation_url"] not in inspected.text


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
            json={"email": "invitee@example.com"},
        )
        manual = await client.post(
            "/api/tutor/invitations",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
            },
            json={"email": "manual-private@example.com"},
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
        student_token = issue_magic_link(
            f"sqlite:///{tmp_path / 'invitations.sqlite3'}",
            "student@example.com",
            15 * 60,
        )
        await client.post(
            "/api/auth/magic-links/confirm", json={"token": student_token}
        )
        inspected = await client.get(
            f"/api/tutor/invitations/{created.json()['id']}"
        )
        retrieved = await client.get(
            f"/api/tutor/invitations/{manual.json()['id']}/link"
        )
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert inspected.status_code == 401
    assert retrieved.status_code == 401
    assert created.json()["invitation_url"] not in inspected.text
    assert manual.json()["invitation_url"] not in retrieved.text


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
            json={"email": "invitee@example.com"},
        )
        client.cookies.clear()
        opened = await client.get(created.json()["invitation_url"])
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert opened.status_code == 200
    assert opened.json() == {"email": "invitee@example.com"}


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
            json={"email": "typo@example.com"},
        )
        corrected = await client.patch(
            f"/api/tutor/invitations/{created.json()['id']}",
            headers=headers,
            json={"email": "  Corrected@Example.COM "},
        )
        opened = await client.get(created.json()["invitation_url"])
    finally:
        await client.aclose()
    get_settings.cache_clear()

    assert corrected.status_code == 200
    assert corrected.json() == {
        "id": created.json()["id"],
        "email": "corrected@example.com",
        "status": "created",
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
            json={"email": "invitee@example.com"},
        )
        revoked = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/revoke",
            headers=headers,
        )
        reopened = await client.get(created.json()["invitation_url"])
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
            json={"email": "invitee@example.com"},
        )
        regenerated = await client.post(
            f"/api/tutor/invitations/{created.json()['id']}/regenerate",
            headers=headers,
        )
        prior_link = await client.get(created.json()["invitation_url"])
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
    assert regenerated.json()["invitation_url"] != created.json()["invitation_url"]
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
            json={"email": "invitee@example.com"},
        )
        token = created.json()["invitation_url"].rsplit("/", 1)[-1]
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

    async def create(email: str) -> tuple[str, str]:
        created = await client.post(
            "/api/tutor/invitations",
            headers=headers,
            json={"email": email},
        )
        return created.json()["id"], created.json()["invitation_url"]

    try:
        revoked_id, revoked_url = await create("revoked@example.com")
        await client.post(
            f"/api/tutor/invitations/{revoked_id}/revoke", headers=headers
        )

        superseded_id, superseded_url = await create("superseded@example.com")
        await client.post(
            f"/api/tutor/invitations/{superseded_id}/regenerate", headers=headers
        )

        expired_id, expired_url = await create("expired@example.com")
        _claimed_id, claimed_url = await create("claimed@example.com")
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
        finally:
            engine.dispose()

        claimed_token = claimed_url.rsplit("/", 1)[-1]
        claimed = await client.post(
            f"/api/invitations/{claimed_token}/claim",
            json={"display_name": "Claimed Student"},
        )
        assert claimed.status_code == 200

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
