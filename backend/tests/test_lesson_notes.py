from datetime import datetime, timezone

import httpx
import pytest


async def note_clients(testbed):
    database_url = testbed.migrated("notes")
    testbed.seed(
        database_url,
        "INSERT INTO accounts (id, email, role, display_name) VALUES "
        "('tutor', 'tutor@example.com', 'tutor', NULL), "
        "('student', 'student@example.com', 'student', 'Student'), "
        "('other', 'other@example.com', 'student', 'Other')",
        *[
            (
                "INSERT INTO bookings (id, student_account_id, start_at, end_at, status, funding_kind, "
                "idempotency_key, created_at) VALUES (:id, :student, :start, :end, :status, "
                "'complimentary', :id, CURRENT_TIMESTAMP)",
                {"id": booking_id, "student": student_id, "start": start, "end": end, "status": status},
            )
            for booking_id, student_id, status, start, end in [
                ("past", "student", "past", "2026-07-17 14:00:00", "2026-07-17 15:00:00"),
                ("future", "student", "upcoming", "2026-07-20 14:00:00", "2026-07-20 15:00:00"),
                ("cancelled", "student", "cancelled", "2026-07-17 16:00:00", "2026-07-17 17:00:00"),
            ]
        ],
    )
    app = testbed.app(now=lambda: datetime(2026, 7, 18, 8, tzinfo=timezone.utc))
    transport = httpx.ASGITransport(app=app)
    tutor, tutor_csrf = await testbed.authenticate(
        transport, database_url, "tutor@example.com"
    )
    student, _ = await testbed.authenticate(
        transport, database_url, "student@example.com"
    )
    other, _ = await testbed.authenticate(transport, database_url, "other@example.com")
    return tutor, tutor_csrf, student, other, database_url


@pytest.mark.anyio
async def test_draft_publish_edit_download_and_confirmed_delete(testbed) -> None:
    tutor, csrf, student, other, database_url = await note_clients(testbed)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf}

    draft = await tutor.put(
        "/api/tutor/bookings/past/lesson-note", headers=headers,
        json={"title": "Algebra Basics", "markdown_source": "# Review\n<script>alert(1)</script>\nUse **factoring**."},
    )
    private = await student.get("/api/student/lesson-notes")
    published = await tutor.post("/api/tutor/bookings/past/lesson-note/publish", headers=headers)
    shared = await student.get("/api/student/lesson-notes")
    other_shared = await other.get("/api/student/lesson-notes")
    edited = await tutor.put(
        "/api/tutor/bookings/past/lesson-note", headers=headers,
        json={"title": "Algebra Basics", "markdown_source": "# Updated\nNo raw HTML."},
    )
    updated = await student.get("/api/student/lesson-notes")
    downloaded = await student.get("/api/student/lesson-notes/past/download")
    rejected_delete = await tutor.request(
        "DELETE", "/api/tutor/bookings/past/lesson-note", headers=headers, json={"confirmed": False}
    )
    deleted = await tutor.request(
        "DELETE", "/api/tutor/bookings/past/lesson-note", headers=headers, json={"confirmed": True}
    )
    after_delete = await student.get("/api/student/lesson-notes")
    evidence = testbed.fetch_all(
        database_url,
        "SELECT deleted_at, markdown_source FROM lesson_notes WHERE booking_id = 'past'",
    )[0]

    assert draft.status_code == 200 and draft.json()["status"] == "draft"
    assert private.json()["lesson_notes"] == []
    assert published.json()["status"] == "published"
    assert shared.json()["lesson_notes"][0]["booking_date"] == "2026-07-17"
    assert "<script>" in shared.json()["lesson_notes"][0]["markdown_source"]
    assert other_shared.json()["lesson_notes"] == []
    assert edited.json()["id"] == draft.json()["id"]
    assert updated.json()["lesson_notes"][0]["markdown_source"] == "# Updated\nNo raw HTML."
    assert downloaded.headers["content-disposition"] == 'attachment; filename="2026-07-17-algebra-basics.md"'
    assert downloaded.text == "# Updated\nNo raw HTML."
    assert rejected_delete.status_code == 422
    assert deleted.status_code == 204
    assert after_delete.json()["lesson_notes"] == []
    assert evidence[0] is not None and evidence[1] == ""


@pytest.mark.anyio
async def test_notes_require_past_non_cancelled_booking_and_bounded_content(testbed) -> None:
    tutor, csrf, student, other, _ = await note_clients(testbed)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf}

    future = await tutor.put(
        "/api/tutor/bookings/future/lesson-note", headers=headers,
        json={"title": "Future", "markdown_source": "Not yet"},
    )
    cancelled = await tutor.put(
        "/api/tutor/bookings/cancelled/lesson-note", headers=headers,
        json={"title": "Cancelled", "markdown_source": "Never"},
    )
    blank_title = await tutor.put(
        "/api/tutor/bookings/past/lesson-note", headers=headers,
        json={"title": "   ", "markdown_source": "Text"},
    )
    too_large = await tutor.put(
        "/api/tutor/bookings/past/lesson-note", headers=headers,
        json={"title": "Large", "markdown_source": "x" * (100 * 1024 + 1)},
    )
    attachment = await tutor.put(
        "/api/tutor/bookings/past/lesson-note", headers=headers,
        json={"title": "Attachment", "markdown_source": "Text", "attachments": ["file.pdf"]},
    )
    student_denied = await student.put(
        "/api/tutor/bookings/past/lesson-note",
        headers={"Origin": "http://testserver", "X-CSRF-Token": "wrong"},
        json={"title": "Denied", "markdown_source": "Text"},
    )

    assert future.status_code == cancelled.status_code == 409
    assert blank_title.status_code == too_large.status_code == attachment.status_code == 422
    assert student_denied.status_code == 403
