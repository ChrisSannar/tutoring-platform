import pytest


async def authenticated_tutor(testbed):
    database_url = testbed.migrated("tutor-settings")
    testbed.seed(
        database_url,
        "INSERT INTO accounts (id, email, role) "
        "VALUES ('tutor-account', 'tutor@example.com', 'tutor')",
    )
    client = testbed.client()
    return client, await testbed.outbox_sign_in(client)


@pytest.mark.anyio
async def test_tutor_views_and_updates_authoritative_business_settings(testbed) -> None:
    client, csrf_token = await authenticated_tutor(testbed)

    initial = await client.get("/api/tutor/settings")
    updated = await client.put(
        "/api/tutor/settings",
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": csrf_token,
        },
        json={
            "tutor_timezone": "America/New_York",
            "default_meeting_details": "https://meet.example.com/avery",
        },
    )
    current = await client.get("/api/tutor/settings")

    assert initial.json() == {
        "tutor_timezone": "America/Chicago",
        "default_meeting_details": None,
    }
    assert updated.status_code == 200
    assert current.json() == updated.json()


@pytest.mark.anyio
async def test_settings_reject_invalid_or_untrusted_updates_without_partial_change(
    testbed,
) -> None:
    client, csrf_token = await authenticated_tutor(testbed)
    database_url = testbed.database_url("tutor-settings")
    valid_payload = {
        "tutor_timezone": "America/New_York",
        "default_meeting_details": "Remote details",
    }

    missing_origin = await client.put(
        "/api/tutor/settings",
        headers={"X-CSRF-Token": csrf_token},
        json=valid_payload,
    )
    invalid_timezone = await client.put(
        "/api/tutor/settings",
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": csrf_token,
        },
        json={**valid_payload, "tutor_timezone": "Central Standard Time"},
    )
    obsolete_price = await client.put(
        "/api/tutor/settings",
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": csrf_token,
        },
        json={**valid_payload, "session_price_cents": 8250},
    )
    unchanged = await client.get("/api/tutor/settings")
    testbed.seed(
        database_url,
        "INSERT INTO accounts (id, email, role, display_name) "
        "VALUES ('student-account', 'student@example.com', 'student', 'Student')",
    )
    student_csrf = await testbed.sign_in(
        client, database_url, "student@example.com"
    )
    student_read = await client.get("/api/tutor/settings")
    student_write = await client.put(
        "/api/tutor/settings",
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": student_csrf,
        },
        json=valid_payload,
    )
    client.cookies.clear()
    anonymous = await client.get("/api/tutor/settings")

    assert missing_origin.status_code == 403
    assert invalid_timezone.status_code == 422
    assert obsolete_price.status_code == 422
    assert unchanged.json()["tutor_timezone"] == "America/Chicago"
    assert student_read.status_code == 401
    assert student_write.status_code == 403
    assert anonymous.status_code == 401
