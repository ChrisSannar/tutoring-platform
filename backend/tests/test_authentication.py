from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from app.main import create_app


def test_repository_command_bootstraps_exactly_one_tutor(testbed) -> None:
    database_url = testbed.database_url("authentication")
    testbed.migrate(database_url)

    first = testbed.bootstrap_tutor(database_url, "Tutor@Example.com", check=False)
    second = testbed.bootstrap_tutor(database_url, "other@example.com", check=False)

    assert first.returncode == 0
    assert first.stdout.strip() == "Tutor created for tutor@example.com"
    assert second.returncode == 1
    assert second.stderr.strip() == "A Tutor already exists"


@pytest.mark.anyio
async def test_magic_link_requests_do_not_reveal_whether_an_account_exists(
    testbed,
) -> None:
    database_url = testbed.migrated("enumeration", origin=None)
    testbed.bootstrap_tutor(database_url)
    client = testbed.client()

    known = await client.post(
        "/api/auth/magic-links", json={"email": " Tutor@Example.com "}
    )
    unknown = await client.post(
        "/api/auth/magic-links", json={"email": "unknown@example.com"}
    )

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json() == {
        "status": "accepted",
        "message": "If the address is eligible, a sign-in link has been sent.",
    }


@pytest.mark.anyio
async def test_eligible_tutor_receives_a_magic_link_in_the_development_outbox(
    testbed,
) -> None:
    database_url = testbed.migrated("outbox", origin=None)
    testbed.bootstrap_tutor(database_url)
    client = testbed.client()

    await client.post(
        "/api/auth/magic-links", json={"email": "tutor@example.com"}
    )
    outbox = await client.get("/api/development/outbox")

    assert outbox.status_code == 200
    messages = outbox.json()["messages"]
    assert len(messages) == 1
    assert messages[0]["to"] == "tutor@example.com"
    assert messages[0]["magic_link"].startswith("/tutor/sign-in/confirm?token=")


@pytest.mark.anyio
async def test_opening_a_magic_link_requires_confirmation_without_consuming_it(
    testbed,
) -> None:
    database_url = testbed.migrated("confirmation", origin=None)
    testbed.bootstrap_tutor(database_url)
    client = testbed.client()

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

    assert first_open.status_code == second_open.status_code == 200
    assert first_open.json() == second_open.json() == {
        "status": "confirmation_required"
    }
    assert "tutoring_session" not in first_open.cookies


@pytest.mark.anyio
async def test_confirming_a_magic_link_once_creates_a_secure_tutor_session(
    testbed,
) -> None:
    database_url = testbed.migrated("session", origin=None)
    testbed.bootstrap_tutor(database_url)
    client = testbed.client()

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
    testbed,
) -> None:
    testbed.migrated("email-limit", origin=None)
    client = testbed.client()

    responses = [
        await client.post(
            "/api/auth/magic-links", json={"email": "same@example.com"}
        )
        for _ in range(6)
    ]

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
    testbed,
) -> None:
    testbed.migrated("ip-limit", origin=None)
    client = testbed.client()

    responses = [
        await client.post(
            "/api/auth/magic-links", json={"email": f"person-{index}@example.com"}
        )
        for index in range(21)
    ]

    assert [response.status_code for response in responses] == [202] * 20 + [429]


@pytest.mark.anyio
async def test_magic_link_expires_after_its_configured_fifteen_minute_window(
    testbed, monkeypatch
) -> None:
    monkeypatch.setenv("TUTORING_MAGIC_LINK_TTL_SECONDS", "0")
    database_url = testbed.migrated("expired-link", origin=None)
    testbed.bootstrap_tutor(database_url)
    client = testbed.client()

    await client.post(
        "/api/auth/magic-links", json={"email": "tutor@example.com"}
    )
    outbox = await client.get("/api/development/outbox")
    magic_link = outbox.json()["messages"][0]["magic_link"]
    token = parse_qs(urlparse(magic_link).query)["token"][0]
    expired = await client.post(
        "/api/auth/magic-links/confirm", json={"token": token}
    )

    assert expired.status_code == 400
    assert expired.json().keys() == {"code", "message", "request_id"}


@pytest.mark.anyio
async def test_logout_requires_same_origin_and_csrf_then_revokes_the_session(
    testbed,
) -> None:
    database_url = testbed.migrated("logout")
    testbed.bootstrap_tutor(database_url)
    client = testbed.client()
    csrf_token = await testbed.outbox_sign_in(client)

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

    assert missing_origin.status_code == 403
    assert foreign_origin.status_code == 403
    assert missing_csrf.status_code == 403
    assert logged_out.status_code == 204
    assert after_logout.status_code == 401


@pytest.mark.anyio
async def test_production_logout_clears_host_cookies(testbed, monkeypatch) -> None:
    database_url = testbed.database_url("production-logout")
    testbed.migrate(database_url)
    testbed.bootstrap_tutor(database_url)
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "production")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "https://testserver")
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=testbed.app()),
        base_url="https://testserver",
        headers={"Origin": "https://testserver"},
    )
    csrf_token = await testbed.sign_in(client, database_url, "tutor@example.com")

    logged_out = await client.post(
        "/api/auth/logout", headers={"X-CSRF-Token": csrf_token}
    )

    cookies = logged_out.headers.get_list("set-cookie")
    assert logged_out.status_code == 204
    assert len(cookies) == 2
    assert all("Max-Age=0" in cookie and "Secure" in cookie for cookie in cookies)


@pytest.mark.anyio
async def test_tutor_session_expires_after_the_inactivity_limit(
    testbed, monkeypatch
) -> None:
    monkeypatch.setenv("TUTORING_SESSION_INACTIVITY_SECONDS", "0")
    database_url = testbed.migrated("inactive-session", origin=None)
    testbed.bootstrap_tutor(database_url)
    client = testbed.client()
    await testbed.outbox_sign_in(client)

    session = await client.get("/api/tutor/session")

    assert session.status_code == 401


@pytest.mark.anyio
async def test_tutor_session_never_survives_its_absolute_limit(
    testbed, monkeypatch
) -> None:
    monkeypatch.setenv("TUTORING_SESSION_ABSOLUTE_SECONDS", "0")
    database_url = testbed.migrated("absolute-session", origin=None)
    testbed.bootstrap_tutor(database_url)
    client = testbed.client()
    await testbed.outbox_sign_in(client)

    session = await client.get("/api/tutor/session")

    assert session.status_code == 401


@pytest.mark.anyio
async def test_authentication_rotates_and_revokes_the_previous_session(
    testbed,
) -> None:
    database_url = testbed.migrated("rotation", origin=None)
    testbed.bootstrap_tutor(database_url)
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

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
    old_client = httpx.AsyncClient(
        transport=old_transport,
        base_url="http://testserver",
        cookies={"tutoring_session": old_session},
    )
    old_session_response = await old_client.get("/api/tutor/session")

    assert second_auth.cookies["tutoring_session"] != old_session
    assert old_session_response.status_code == 401
