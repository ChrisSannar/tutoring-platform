import asyncio

import pytest


async def student_directory_client(testbed, role: str = "tutor"):
    database_url = testbed.migrated("students")
    testbed.seed(
        database_url,
        "INSERT INTO accounts (id, email, role, display_name) VALUES "
        "('tutor', 'tutor@example.com', 'tutor', NULL), "
        "('student-a', 'avery@example.com', 'student', 'Avery Chen'), "
        "('student-b', 'bailey@example.com', 'student', 'Bailey Jones')",
    )
    client = testbed.client()
    email = "tutor@example.com" if role == "tutor" else "avery@example.com"
    await testbed.sign_in(client, database_url, email)
    return client


@pytest.mark.anyio
async def test_tutor_reads_an_allowlisted_student_detail_with_bounded_summaries(
    testbed,
) -> None:
    client = await student_directory_client(testbed)

    listed = await client.get("/api/tutor/students")
    detail = await client.get("/api/tutor/students/student-a")

    assert listed.json()["students"][0] == {
        "id": "student-a",
        "email": "avery@example.com",
        "display_name": "Avery Chen",
    }
    assert detail.json() == {
        "id": "student-a",
        "email": "avery@example.com",
        "display_name": "Avery Chen",
        "funding": {"session_credits": 0},
        "upcoming_booking": None,
    }


@pytest.mark.anyio
async def test_student_cannot_read_the_tutor_student_directory_or_detail(
    testbed,
) -> None:
    client = await student_directory_client(testbed, role="student-a")

    listed = await client.get("/api/tutor/students")
    detail = await client.get("/api/tutor/students/student-b")
    credit_change = await client.post(
        "/api/tutor/students/student-b/credits",
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": client.cookies["tutoring_csrf"],
            "Idempotency-Key": "student-forbidden",
        },
        json={"quantity": 1, "reason": "Not allowed"},
    )

    assert listed.status_code == 401
    assert detail.status_code == 401
    assert credit_change.status_code == 403
    assert "bailey@example.com" not in detail.text


@pytest.mark.anyio
async def test_tutor_adjustments_append_an_idempotent_credit_ledger(testbed) -> None:
    client = await student_directory_client(testbed)
    base_headers = {
        "Origin": "http://testserver",
        "X-CSRF-Token": client.cookies["tutoring_csrf"],
    }

    granted = await client.post(
        "/api/tutor/students/student-a/credits",
        headers={**base_headers, "Idempotency-Key": "grant-two"},
        json={"quantity": 2, "reason": "Tutor credit grant"},
    )
    retried = await client.post(
        "/api/tutor/students/student-a/credits",
        headers={**base_headers, "Idempotency-Key": "grant-two"},
        json={"quantity": 2, "reason": "Tutor credit grant"},
    )
    deducted = await client.post(
        "/api/tutor/students/student-a/credits",
        headers={**base_headers, "Idempotency-Key": "deduct-one"},
        json={"quantity": -1, "reason": "Correct duplicate grant"},
    )
    detail = await client.get("/api/tutor/students/student-a")
    ledger = await client.get("/api/tutor/students/student-a/credit-ledger")

    assert granted.status_code == 200
    assert granted.json()["session_credits"] == 2
    assert retried.json() == granted.json()
    assert deducted.json()["session_credits"] == 1
    assert detail.json()["funding"]["session_credits"] == 1
    assert [event["quantity"] for event in ledger.json()["events"]] == [2, -1]
    assert [event["event_type"] for event in ledger.json()["events"]] == [
        "credit_adjustment",
        "credit_adjustment",
    ]
    assert [event["reason"] for event in ledger.json()["events"]] == [
        "Tutor credit grant",
        "Correct duplicate grant",
    ]


@pytest.mark.anyio
async def test_credit_adjustments_require_reason_and_never_create_negative_value(
    testbed,
) -> None:
    client = await student_directory_client(testbed)
    headers = {
        "Origin": "http://testserver",
        "X-CSRF-Token": client.cookies["tutoring_csrf"],
    }

    missing_reason = await client.post(
        "/api/tutor/students/student-a/credits",
        headers={**headers, "Idempotency-Key": "missing-reason"},
        json={"quantity": 1, "reason": "   "},
    )
    too_large_deduction = await client.post(
        "/api/tutor/students/student-a/credits",
        headers={**headers, "Idempotency-Key": "negative"},
        json={"quantity": -1, "reason": "No available ordinary credit"},
    )
    detail = await client.get("/api/tutor/students/student-a")

    assert missing_reason.status_code == 422
    assert too_large_deduction.status_code == 409
    assert detail.json()["funding"]["session_credits"] == 0


@pytest.mark.anyio
async def test_concurrent_deductions_can_spend_one_credit_only_once(testbed) -> None:
    client = await student_directory_client(testbed)
    headers = {
        "Origin": "http://testserver",
        "X-CSRF-Token": client.cookies["tutoring_csrf"],
    }

    await client.post(
        "/api/tutor/students/student-a/credits",
        headers={**headers, "Idempotency-Key": "one-credit"},
        json={"quantity": 1, "reason": "One available credit"},
    )
    deductions = await asyncio.gather(
        client.post(
            "/api/tutor/students/student-a/credits",
            headers={**headers, "Idempotency-Key": "spend-a"},
            json={"quantity": -1, "reason": "First spend"},
        ),
        client.post(
            "/api/tutor/students/student-a/credits",
            headers={**headers, "Idempotency-Key": "spend-b"},
            json={"quantity": -1, "reason": "Competing spend"},
        ),
    )
    detail = await client.get("/api/tutor/students/student-a")

    assert sorted(response.status_code for response in deductions) == [200, 409]
    assert detail.json()["funding"]["session_credits"] == 0
