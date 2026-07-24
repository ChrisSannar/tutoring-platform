import pytest


async def inquiry_client(testbed):
    testbed.migrated("inquiries")
    return testbed.client()


async def authenticate(testbed, client, database_url: str, role: str, email: str) -> str:
    testbed.seed(
        database_url,
        (
            "INSERT INTO accounts (id, email, role, display_name) "
            "VALUES (:id, :email, :role, :display_name)",
            {
                "id": f"{role}-account",
                "email": email,
                "role": role,
                "display_name": "Student" if role == "student" else None,
            },
        ),
    )
    return await testbed.sign_in(client, database_url, email)


@pytest.mark.anyio
async def test_prospect_submits_a_normalized_inquiry_without_receiving_private_state(
    testbed,
) -> None:
    client = await inquiry_client(testbed)

    response = await client.post(
        "/api/inquiries",
        json={
            "email": "  Prospect@Example.COM ",
            "message": "  I would like help preparing for calculus.  ",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "message": "Thanks. Your tutoring request has been received."
    }


@pytest.mark.anyio
async def test_tutor_lists_each_active_inquiry_with_an_allowlisted_response(
    testbed,
) -> None:
    client = await inquiry_client(testbed)
    database_url = testbed.database_url("inquiries")

    await client.post(
        "/api/inquiries",
        json={"email": " One@Example.COM ", "message": " First context "},
    )
    await client.post(
        "/api/inquiries",
        json={"email": "one@example.com", "message": "Second context"},
    )
    await authenticate(testbed, client, database_url, "tutor", "tutor@example.com")
    response = await client.get("/api/tutor/inquiries")

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
    testbed,
) -> None:
    client = await inquiry_client(testbed)

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
async def test_tutor_archives_an_inquiry_out_of_the_active_queue(testbed) -> None:
    client = await inquiry_client(testbed)
    database_url = testbed.database_url("inquiries")

    await client.post(
        "/api/inquiries",
        json={"email": "archive@example.com", "message": "Not ready yet"},
    )
    csrf_token = await authenticate(
        testbed, client, database_url, "tutor", "tutor@example.com"
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

    assert archived.status_code == 204
    assert remaining.json() == {"inquiries": []}


@pytest.mark.anyio
async def test_tutor_must_explicitly_confirm_permanent_inquiry_deletion(testbed) -> None:
    client = await inquiry_client(testbed)
    database_url = testbed.database_url("inquiries")

    await client.post(
        "/api/inquiries",
        json={"email": "delete@example.com", "message": "Remove my data"},
    )
    csrf_token = await authenticate(
        testbed, client, database_url, "tutor", "tutor@example.com"
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

    assert unconfirmed.status_code == 422
    assert deleted.status_code == 204
    assert remaining.json() == {"inquiries": []}


@pytest.mark.anyio
async def test_invalid_public_inquiry_returns_a_sanitized_validation_error(
    testbed,
) -> None:
    client = await inquiry_client(testbed)

    responses = [
        await client.post("/api/inquiries", json=payload)
        for payload in (
            {"email": "not-an-email", "message": "private invalid context"},
            {"email": "valid@example.com", "message": "   "},
            {"email": "valid@example.com", "message": "x" * 2001},
        )
    ]

    assert [response.status_code for response in responses] == [422, 422, 422]
    assert all(
        response.json().keys() == {"code", "message", "request_id"}
        for response in responses
    )
    assert "private invalid context" not in responses[0].text
    assert "x" * 2001 not in responses[2].text


@pytest.mark.anyio
async def test_anonymous_and_student_callers_cannot_read_or_mutate_inquiries(
    testbed,
) -> None:
    client = await inquiry_client(testbed)
    database_url = testbed.database_url("inquiries")

    await client.post(
        "/api/inquiries",
        json={"email": "private@example.com", "message": "Private context"},
    )
    anonymous = await client.get("/api/tutor/inquiries")
    tutor_csrf = await authenticate(
        testbed, client, database_url, "tutor", "tutor@example.com"
    )
    tutor_list = await client.get("/api/tutor/inquiries")
    inquiry_id = tutor_list.json()["inquiries"][0]["id"]
    student_csrf = await authenticate(
        testbed, client, database_url, "student", "student@example.com"
    )
    student_list = await client.get("/api/tutor/inquiries")
    student_archive = await client.post(
        f"/api/tutor/inquiries/{inquiry_id}/archive",
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": student_csrf,
        },
    )

    assert tutor_csrf
    assert anonymous.status_code == 401
    assert student_list.status_code == 401
    assert student_archive.status_code == 403
    assert "private@example.com" not in anonymous.text
    assert "Private context" not in student_list.text
