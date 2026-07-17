from pathlib import Path
from urllib.parse import parse_qs, urlparse

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


async def inquiry_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> httpx.AsyncClient:
    database_url = f"sqlite:///{tmp_path / 'inquiries.sqlite3'}"
    alembic_config = Config("backend/alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    get_settings.cache_clear()
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()),
        base_url="http://testserver",
    )


async def authenticate(
    client: httpx.AsyncClient, database_url: str, role: str, email: str
) -> str:
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
                    "display_name": "Student" if role == "student" else None,
                },
            )
    finally:
        engine.dispose()
    await client.post("/api/auth/magic-links", json={"email": email})
    outbox = await client.get("/api/development/outbox")
    token = parse_qs(urlparse(outbox.json()["messages"][-1]["magic_link"]).query)[
        "token"
    ][0]
    confirmed = await client.post(
        "/api/auth/magic-links/confirm", json={"token": token}
    )
    return confirmed.json()["csrf_token"]


@pytest.mark.anyio
async def test_prospect_submits_a_normalized_inquiry_without_receiving_private_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await inquiry_client(monkeypatch, tmp_path)
    try:
        response = await client.post(
            "/api/inquiries",
            json={
                "email": "  Prospect@Example.COM ",
                "message": "  I would like help preparing for calculus.  ",
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 202
    assert response.json() == {
        "message": "Thanks. Your tutoring request has been received."
    }


@pytest.mark.anyio
async def test_tutor_lists_each_active_inquiry_with_an_allowlisted_response(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await inquiry_client(monkeypatch, tmp_path)
    database_url = get_settings().database_url
    try:
        await client.post(
            "/api/inquiries",
            json={"email": " One@Example.COM ", "message": " First context "},
        )
        await client.post(
            "/api/inquiries",
            json={"email": "one@example.com", "message": "Second context"},
        )
        await authenticate(client, database_url, "tutor", "tutor@example.com")
        response = await client.get("/api/tutor/inquiries")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {
        "inquiries": [
            {
                "id": response.json()["inquiries"][0]["id"],
                "email": "one@example.com",
                "message": "First context",
                "status": "new",
            },
            {
                "id": response.json()["inquiries"][1]["id"],
                "email": "one@example.com",
                "message": "Second context",
                "status": "new",
            },
        ]
    }


@pytest.mark.anyio
async def test_public_inquiries_are_limited_to_five_per_hashed_ip_each_hour(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await inquiry_client(monkeypatch, tmp_path)
    try:
        responses = [
            await client.post(
                "/api/inquiries",
                json={
                    "email": f"prospect-{index}@example.com",
                    "message": f"Context {index}",
                },
            )
            for index in range(6)
        ]
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert [response.status_code for response in responses] == [
        202,
        202,
        202,
        202,
        202,
        429,
    ]
    assert responses[-1].json().keys() == {"code", "message", "request_id"}
    assert responses[-1].json()["message"] == "Request failed"


@pytest.mark.anyio
async def test_tutor_archives_an_inquiry_out_of_the_active_queue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await inquiry_client(monkeypatch, tmp_path)
    database_url = get_settings().database_url
    try:
        await client.post(
            "/api/inquiries",
            json={"email": "archive@example.com", "message": "Not ready yet"},
        )
        csrf_token = await authenticate(
            client, database_url, "tutor", "tutor@example.com"
        )
        active = await client.get("/api/tutor/inquiries")
        inquiry_id = active.json()["inquiries"][0]["id"]
        archived = await client.post(
            f"/api/tutor/inquiries/{inquiry_id}/archive",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": csrf_token,
            },
        )
        remaining = await client.get("/api/tutor/inquiries")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert archived.status_code == 204
    assert remaining.json() == {"inquiries": []}


@pytest.mark.anyio
async def test_tutor_must_explicitly_confirm_permanent_inquiry_deletion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await inquiry_client(monkeypatch, tmp_path)
    database_url = get_settings().database_url
    try:
        await client.post(
            "/api/inquiries",
            json={"email": "delete@example.com", "message": "Remove my data"},
        )
        csrf_token = await authenticate(
            client, database_url, "tutor", "tutor@example.com"
        )
        active = await client.get("/api/tutor/inquiries")
        inquiry_id = active.json()["inquiries"][0]["id"]
        headers = {
            "Origin": "http://testserver",
            "X-CSRF-Token": csrf_token,
        }
        unconfirmed = await client.request(
            "DELETE",
            f"/api/tutor/inquiries/{inquiry_id}",
            headers=headers,
            json={"confirmed": False},
        )
        deleted = await client.request(
            "DELETE",
            f"/api/tutor/inquiries/{inquiry_id}",
            headers=headers,
            json={"confirmed": True},
        )
        remaining = await client.get("/api/tutor/inquiries")
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert unconfirmed.status_code == 422
    assert deleted.status_code == 204
    assert remaining.json() == {"inquiries": []}


@pytest.mark.anyio
async def test_invalid_public_inquiry_returns_a_sanitized_validation_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await inquiry_client(monkeypatch, tmp_path)
    try:
        responses = [
            await client.post("/api/inquiries", json=payload)
            for payload in (
                {"email": "not-an-email", "message": "private invalid context"},
                {"email": "valid@example.com", "message": "   "},
                {"email": "valid@example.com", "message": "x" * 2001},
            )
        ]
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert [response.status_code for response in responses] == [422, 422, 422]
    assert all(
        response.json().keys() == {"code", "message", "request_id"}
        for response in responses
    )
    assert "private invalid context" not in responses[0].text
    assert "x" * 2001 not in responses[2].text


@pytest.mark.anyio
async def test_anonymous_and_student_callers_cannot_read_or_mutate_inquiries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = await inquiry_client(monkeypatch, tmp_path)
    database_url = get_settings().database_url
    try:
        await client.post(
            "/api/inquiries",
            json={"email": "private@example.com", "message": "Private context"},
        )
        anonymous = await client.get("/api/tutor/inquiries")
        tutor_csrf = await authenticate(
            client, database_url, "tutor", "tutor@example.com"
        )
        tutor_list = await client.get("/api/tutor/inquiries")
        inquiry_id = tutor_list.json()["inquiries"][0]["id"]
        student_csrf = await authenticate(
            client, database_url, "student", "student@example.com"
        )
        student_list = await client.get("/api/tutor/inquiries")
        student_archive = await client.post(
            f"/api/tutor/inquiries/{inquiry_id}/archive",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": student_csrf,
            },
        )
    finally:
        await client.aclose()
        get_settings.cache_clear()

    assert tutor_csrf
    assert anonymous.status_code == 401
    assert student_list.status_code == 401
    assert student_archive.status_code == 403
    assert "private@example.com" not in anonymous.text
    assert "Private context" not in student_list.text
