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


async def collected_pilot_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[httpx.AsyncClient, str, httpx.AsyncClient, str, str]:
    database_url = f"sqlite:///{tmp_path / 'pilot-data-deletion.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
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
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    get_settings.cache_clear()

    tutor = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()),
        base_url="http://testserver",
    )
    await tutor.post("/api/auth/magic-links", json={"email": "tutor@example.com"})
    tutor_outbox = await tutor.get("/api/development/outbox")
    tutor_token = parse_qs(
        urlparse(tutor_outbox.json()["messages"][-1]["magic_link"]).query
    )["token"][0]
    tutor_sign_in = await tutor.post(
        "/api/auth/magic-links/confirm", json={"token": tutor_token}
    )
    tutor_csrf = tutor_sign_in.json()["csrf_token"]
    tutor_headers = {
        "Origin": "http://testserver",
        "X-CSRF-Token": tutor_csrf,
    }
    invitation = await tutor.post(
        "/api/tutor/invitations",
        headers=tutor_headers,
        json={
            "email": "student@example.com",
            "display_name": "Avery",
            "shared_personal_message": "Welcome to tutoring.",
            "private_tutor_note": "Needs evening availability.",
        },
    )
    activated = await tutor.post(
        f"/api/tutor/invitations/{invitation.json()['id']}/activate",
        headers=tutor_headers,
    )
    invitation_token = activated.json()["invitation_url"].removeprefix("/invite/")

    student = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()),
        base_url="http://testserver",
    )
    await student.post(
        f"/api/invitations/{invitation_token}/magic-links",
        json={"email": "student@example.com"},
    )
    student_outbox = await student.get("/api/development/outbox")
    claim_token = parse_qs(
        urlparse(student_outbox.json()["messages"][-1]["magic_link"]).query
    )["token"][0]
    claimed = await student.post(
        "/api/invitation-claims/confirm",
        json={"token": claim_token, "display_name": "Avery Chen"},
    )
    student_csrf = claimed.json()["csrf_token"]
    students = await tutor.get("/api/tutor/students")
    student_id = students.json()["students"][0]["id"]
    return tutor, tutor_csrf, student, student_csrf, student_id


@pytest.mark.anyio
async def test_tutor_deliberately_deletes_collected_pilot_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tutor, tutor_csrf, student, _, student_id = await collected_pilot_data(
        monkeypatch, tmp_path
    )
    try:
        deleted = await tutor.request(
            "DELETE",
            f"/api/tutor/students/{student_id}/pilot-data",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": tutor_csrf,
            },
            json={"confirmation": "DELETE COLLECTED DATA"},
        )
        after = await tutor.get("/api/tutor/students")
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert deleted.status_code == 200
    assert deleted.json() == {
        "status": "deleted",
        "removed": {
            "invitations": 1,
            "student_sessions": 1,
            "bookings": 0,
        },
    }
    assert after.json() == {"students": []}


@pytest.mark.anyio
async def test_student_cannot_delete_collected_pilot_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tutor, _, student, student_csrf, student_id = await collected_pilot_data(
        monkeypatch, tmp_path
    )
    try:
        denied = await student.request(
            "DELETE",
            f"/api/tutor/students/{student_id}/pilot-data",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": student_csrf,
            },
            json={"confirmation": "DELETE COLLECTED DATA"},
        )
        still_visible = await tutor.get("/api/tutor/students")
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert denied.status_code == 403
    assert denied.json().keys() == {"code", "message", "request_id"}
    assert len(still_visible.json()["students"]) == 1


@pytest.mark.anyio
async def test_deletion_requires_the_exact_confirmation_phrase(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tutor, tutor_csrf, student, _, student_id = await collected_pilot_data(
        monkeypatch, tmp_path
    )
    try:
        rejected = await tutor.request(
            "DELETE",
            f"/api/tutor/students/{student_id}/pilot-data",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": tutor_csrf,
            },
            json={"confirmation": "delete"},
        )
        still_visible = await tutor.get("/api/tutor/students")
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert rejected.status_code == 400
    assert rejected.json().keys() == {"code", "message", "request_id"}
    assert len(still_visible.json()["students"]) == 1


@pytest.mark.anyio
async def test_deleted_student_session_cannot_access_protected_resources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tutor, tutor_csrf, student, _, student_id = await collected_pilot_data(
        monkeypatch, tmp_path
    )
    try:
        await tutor.request(
            "DELETE",
            f"/api/tutor/students/{student_id}/pilot-data",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": tutor_csrf,
            },
            json={"confirmation": "DELETE COLLECTED DATA"},
        )
        student_session = await student.get("/api/student/session")
        funding = await student.get("/api/student/funding")
    finally:
        await tutor.aclose()
        await student.aclose()
        get_settings.cache_clear()

    assert student_session.status_code == 401
    assert funding.status_code == 401
    assert student_session.json().keys() == {"code", "message", "request_id"}
    assert funding.json().keys() == {"code", "message", "request_id"}
