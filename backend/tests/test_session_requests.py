from pathlib import Path
from urllib.parse import parse_qs, urlparse

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


async def authenticated_client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    role: str,
    email: str,
) -> tuple[httpx.AsyncClient, str]:
    database_url = f"sqlite:///{tmp_path / 'session-requests.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role, display_name) "
                    "VALUES (:id, :email, :role, :display_name)"
                ),
                {
                    "id": f"{role}-account",
                    "email": email,
                    "role": role,
                    "display_name": "Avery" if role == "student" else None,
                },
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
    await client.post("/api/auth/magic-links", json={"email": email})
    outbox = await client.get("/api/development/outbox")
    token = parse_qs(
        urlparse(outbox.json()["messages"][-1]["magic_link"]).query
    )["token"][0]
    authenticated = await client.post(
        "/api/auth/magic-links/confirm", json={"token": token}
    )
    return client, authenticated.json()["csrf_token"]


async def additional_authenticated_client(
    tmp_path: Path,
    role: str,
    email: str,
    account_id: str,
) -> tuple[httpx.AsyncClient, str]:
    database_url = f"sqlite:///{tmp_path / 'session-requests.sqlite3'}"
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role, display_name) "
                    "VALUES (:id, :email, :role, :display_name)"
                ),
                {
                    "id": account_id,
                    "email": email,
                    "role": role,
                    "display_name": "Bailey" if role == "student" else None,
                },
            )
    finally:
        engine.dispose()

    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()),
        base_url="http://testserver",
    )
    await client.post("/api/auth/magic-links", json={"email": email})
    outbox = await client.get("/api/development/outbox")
    token = parse_qs(
        urlparse(outbox.json()["messages"][-1]["magic_link"]).query
    )["token"][0]
    authenticated = await client.post(
        "/api/auth/magic-links/confirm", json={"token": token}
    )
    return client, authenticated.json()["csrf_token"]


@pytest.mark.anyio
async def test_student_submits_a_pending_session_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
                "Idempotency-Key": "request-avery-2026-07-20",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "America/Chicago",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "service": "Algebra tutoring",
        "preferred_start": "2026-07-20T18:00:00Z",
        "timezone": "America/Chicago",
        "message": None,
        "status": "pending",
    }


@pytest.mark.anyio
async def test_session_request_requires_a_service(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
                "Idempotency-Key": "missing-service",
            },
            json={
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "America/Chicago",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 422


@pytest.mark.anyio
async def test_session_request_requires_a_preferred_start(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
                "Idempotency-Key": "missing-preferred-start",
            },
            json={
                "service": "Algebra tutoring",
                "timezone": "America/Chicago",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 422


@pytest.mark.anyio
async def test_session_request_requires_a_timezone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
                "Idempotency-Key": "missing-timezone",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 422


@pytest.mark.anyio
async def test_session_request_rejects_a_non_iana_timezone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
                "Idempotency-Key": "invalid-timezone",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "Central Standard Time",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 422


@pytest.mark.anyio
async def test_session_request_rejects_a_message_over_1000_characters(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
                "Idempotency-Key": "long-message",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "America/Chicago",
                "message": "x" * 1001,
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 422


@pytest.mark.anyio
async def test_session_request_normalizes_preferred_start_to_utc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
                "Idempotency-Key": "utc-normalization",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T13:00:00-05:00",
                "timezone": "America/Chicago",
                "message": "Please review quadratic equations.",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 201
    assert response.json()["preferred_start"] == "2026-07-20T18:00:00Z"


@pytest.mark.anyio
async def test_student_retry_returns_the_same_session_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    headers = {
        "Origin": "http://testserver",
        "X-CSRF-Token": csrf_token,
        "Idempotency-Key": "safe-retry",
    }
    submission = {
        "service": "Algebra tutoring",
        "preferred_start": "2026-07-20T13:00:00-05:00",
        "timezone": "America/Chicago",
        "message": "Please review quadratic equations.",
    }
    try:
        first = await client.post(
            "/api/student/session-requests", headers=headers, json=submission
        )
        retry = await client.post(
            "/api/student/session-requests", headers=headers, json=submission
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert first.status_code == retry.status_code == 201
    assert retry.json() == first.json()


@pytest.mark.anyio
async def test_idempotency_key_is_scoped_per_student(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    first_student, first_csrf = await authenticated_client(
        monkeypatch, tmp_path, "student", "first@example.com"
    )
    second_student, second_csrf = await additional_authenticated_client(
        tmp_path, "student", "second@example.com", "second-student-account"
    )
    submission = {
        "service": "Algebra tutoring",
        "preferred_start": "2026-07-20T18:00:00Z",
        "timezone": "America/Chicago",
    }
    try:
        first = await first_student.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": first_csrf,
                "Idempotency-Key": "student-scoped-key",
            },
            json=submission,
        )
        second = await second_student.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": second_csrf,
                "Idempotency-Key": "student-scoped-key",
            },
            json=submission,
        )
    finally:
        await first_student.aclose()
        await second_student.aclose()
        get_settings.cache_clear()

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


@pytest.mark.anyio
async def test_session_request_rejects_a_missing_csrf_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, _ = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "Idempotency-Key": "missing-csrf",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "America/Chicago",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 403


@pytest.mark.anyio
async def test_session_request_rejects_a_foreign_csrf_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, _ = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": "csrf-from-another-student-session",
                "Idempotency-Key": "foreign-csrf",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "America/Chicago",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 403


@pytest.mark.anyio
async def test_session_request_rejects_a_missing_origin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "X-CSRF-Token": csrf_token,
                "Idempotency-Key": "missing-origin",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "America/Chicago",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 403


@pytest.mark.anyio
async def test_student_views_their_session_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        created = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
                "Idempotency-Key": "student-read",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "America/Chicago",
            },
        )
        viewed = await client.get(
            f"/api/student/session-requests/{created.json()['id']}"
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert viewed.status_code == 200
    assert viewed.json() == created.json()


@pytest.mark.anyio
async def test_student_cannot_view_another_students_session_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    first_student, first_csrf = await authenticated_client(
        monkeypatch, tmp_path, "student", "first@example.com"
    )
    second_student, _ = await additional_authenticated_client(
        tmp_path, "student", "second@example.com", "second-student-account"
    )
    try:
        created = await first_student.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": first_csrf,
                "Idempotency-Key": "private-to-first-student",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "America/Chicago",
                "message": "This belongs to the first Student.",
            },
        )
        cross_student_view = await second_student.get(
            f"/api/student/session-requests/{created.json()['id']}"
        )
    finally:
        await first_student.aclose()
        await second_student.aclose()
        get_settings.cache_clear()

    assert cross_student_view.status_code == 404
    assert "This belongs to the first Student." not in cross_student_view.text


@pytest.mark.anyio
async def test_tutor_views_all_business_session_requests(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    first_student, first_csrf = await authenticated_client(
        monkeypatch, tmp_path, "student", "first@example.com"
    )
    second_student, second_csrf = await additional_authenticated_client(
        tmp_path, "student", "second@example.com", "second-student-account"
    )
    tutor, _ = await additional_authenticated_client(
        tmp_path, "tutor", "tutor@example.com", "tutor-account"
    )
    try:
        first = await first_student.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": first_csrf,
                "Idempotency-Key": "first-request",
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "America/Chicago",
            },
        )
        second = await second_student.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": second_csrf,
                "Idempotency-Key": "second-request",
            },
            json={
                "service": "Geometry tutoring",
                "preferred_start": "2026-07-21T19:00:00Z",
                "timezone": "America/New_York",
                "message": "Please cover triangle proofs.",
            },
        )
        visible = await tutor.get("/api/tutor/session-requests")
    finally:
        await first_student.aclose()
        await second_student.aclose()
        await tutor.aclose()
        get_settings.cache_clear()

    assert visible.status_code == 200
    assert visible.json() == {
        "requests": [
            {
                    **first.json(),
                    "student": {
                        "id": "student-account",
                        "email": "first@example.com",
                    "display_name": "Avery",
                },
            },
            {
                    **second.json(),
                    "student": {
                        "id": "second-student-account",
                        "email": "second@example.com",
                    "display_name": "Bailey",
                },
            },
        ]
    }


@pytest.mark.anyio
async def test_session_request_requires_an_idempotency_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, csrf_token = await authenticated_client(
        monkeypatch, tmp_path, "student", "student@example.com"
    )
    try:
        response = await client.post(
            "/api/student/session-requests",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
            },
            json={
                "service": "Algebra tutoring",
                "preferred_start": "2026-07-20T18:00:00Z",
                "timezone": "America/Chicago",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 422
