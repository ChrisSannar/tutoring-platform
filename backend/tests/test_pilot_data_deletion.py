import pytest


async def collected_pilot_data(testbed):
    database_url = testbed.migrated("pilot-data-deletion")
    testbed.bootstrap_tutor(database_url)

    tutor = testbed.client()
    tutor_csrf = await testbed.outbox_sign_in(tutor)
    invitation = await tutor.post(
        "/api/tutor/invitations",
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": tutor_csrf,
        },
        json={"email": "student@example.com"},
    )
    invitation_token = invitation.json()["invitation_url"].removeprefix("/invite/")

    student = testbed.client()
    claimed = await student.post(
        f"/api/invitations/{invitation_token}/claim",
        json={"display_name": "Avery Chen"},
    )
    student_csrf = claimed.json()["csrf_token"]
    students = await tutor.get("/api/tutor/students")
    student_id = students.json()["students"][0]["id"]
    return tutor, tutor_csrf, student, student_csrf, student_id


@pytest.mark.anyio
async def test_tutor_deliberately_deletes_collected_pilot_data(testbed) -> None:
    tutor, tutor_csrf, student, _, student_id = await collected_pilot_data(testbed)

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
async def test_student_cannot_delete_collected_pilot_data(testbed) -> None:
    tutor, _, student, student_csrf, student_id = await collected_pilot_data(testbed)

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

    assert denied.status_code == 403
    assert denied.json().keys() == {"code", "message", "request_id"}
    assert len(still_visible.json()["students"]) == 1


@pytest.mark.anyio
async def test_deletion_requires_the_exact_confirmation_phrase(testbed) -> None:
    tutor, tutor_csrf, student, _, student_id = await collected_pilot_data(testbed)

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

    assert rejected.status_code == 400
    assert rejected.json().keys() == {"code", "message", "request_id"}
    assert len(still_visible.json()["students"]) == 1


@pytest.mark.anyio
async def test_deleted_student_session_cannot_access_protected_resources(testbed) -> None:
    tutor, tutor_csrf, student, _, student_id = await collected_pilot_data(testbed)

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

    assert student_session.status_code == 401
    assert funding.status_code == 401
    assert student_session.json().keys() == {"code", "message", "request_id"}
    assert funding.json().keys() == {"code", "message", "request_id"}
