import pytest


async def authenticated_tutor(testbed):
    database_url = testbed.migrated("uncovered")
    testbed.seed(
        database_url,
        "INSERT INTO accounts (id, email, role) "
        "VALUES ('tutor-account', 'tutor@example.com', 'tutor')",
    )
    client = testbed.client()
    return client, await testbed.outbox_sign_in(client)


@pytest.mark.anyio
async def test_health_reports_ok(testbed) -> None:
    testbed.setenv(testbed.database_url("health"), origin=None)

    response = await testbed.client().get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_role_session_rejects_anonymous_callers(testbed) -> None:
    testbed.setenv(testbed.database_url("anonymous"), origin=None)

    response = await testbed.client().get("/api/auth/session")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_role_session_reports_the_active_role(testbed) -> None:
    client, _ = await authenticated_tutor(testbed)

    response = await client.get("/api/auth/session")

    assert response.status_code == 200
    assert response.json() == {"role": "tutor"}


@pytest.mark.anyio
async def test_testing_clock_overrides_now(testbed) -> None:
    client, csrf_token = await authenticated_tutor(testbed)

    response = await client.post(
        "/api/testing/clock",
        headers={"Origin": "http://testserver", "X-CSRF-Token": csrf_token},
        json={"now": "2026-08-01T12:00:00Z"},
    )

    assert response.status_code == 200
    assert response.json()["now"].startswith("2026-08-01T12:00:00")


@pytest.mark.anyio
async def test_invite_link_opens_the_invitation(testbed) -> None:
    client, csrf_token = await authenticated_tutor(testbed)

    created = await client.post(
        "/api/tutor/invitations",
        headers={"Origin": "http://testserver", "X-CSRF-Token": csrf_token},
        json={"email": "invitee@example.com"},
    )
    opened = await client.get(created.json()["invitation_url"])

    assert created.status_code == 201
    assert opened.status_code == 200
    assert opened.json()["email"] == "invitee@example.com"


@pytest.mark.anyio
async def test_payment_routes_and_schema_are_absent(testbed) -> None:
    client, _ = await authenticated_tutor(testbed)
    database_url = testbed.database_url("uncovered")

    responses = [
        await client.post("/api/student/checkouts"),
        await client.post("/api/stripe/webhook"),
        await client.get("/api/student/refund-requests"),
        await client.get("/api/tutor/refund-requests"),
    ]
    tables = {
        row[0]
        for row in testbed.fetch_all(
            database_url,
            "SELECT name FROM sqlite_master WHERE type = 'table'",
        )
    }

    assert {response.status_code for response in responses} == {404}
    assert tables.isdisjoint(
        {
            "slot_holds",
            "checkout_sessions",
            "stripe_events",
            "payment_evidence",
            "refund_requests",
            "refund_evidence",
        }
    )
