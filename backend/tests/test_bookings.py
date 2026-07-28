from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import httpx
import pytest

from app.funding import student_funding_summary


async def booking_context(testbed):
    database_url = testbed.migrated("bookings")
    testbed.seed(
        database_url,
        "INSERT INTO accounts (id, email, role, display_name) VALUES "
        "('tutor', 'tutor@example.com', 'tutor', NULL), "
        "('student', 'student@example.com', 'student', 'Student'), "
        "('student-2', 'second@example.com', 'student', 'Second Student')",
        "INSERT INTO availability_windows (id, weekday, start_time, end_time) "
        "VALUES ('monday', 0, '09:00', '12:00')",
        "INSERT INTO credit_ledger_entries "
        "(id, student_account_id, event_type, quantity, reason, "
        "idempotency_key, created_at) VALUES "
        "('credit', 'student', 'credit_invitation_grant', 1, "
        "'Invitation Claim', 'credit', CURRENT_TIMESTAMP)",
        "UPDATE tutor_settings SET default_meeting_details = "
        "'Initial meeting room' WHERE id = 1",
    )
    clock = [datetime(2026, 7, 19, 8, tzinfo=timezone.utc)]
    transport = httpx.ASGITransport(app=testbed.app(now=lambda: clock[0]))
    tutor, tutor_csrf = await testbed.authenticate(
        transport, database_url, "tutor@example.com"
    )
    student, student_csrf = await testbed.authenticate(
        transport, database_url, "student@example.com"
    )
    return tutor, tutor_csrf, student, student_csrf, database_url, clock


def headers(csrf: str, key: str) -> dict[str, str]:
    return {
        "Origin": "http://testserver",
        "X-CSRF-Token": csrf,
        "Idempotency-Key": key,
    }


@pytest.mark.anyio
async def test_credit_booking_consumes_replenishes_and_schedules_again(testbed) -> None:
    tutor, _, student, csrf, _, clock = await booking_context(testbed)

    created = await student.post(
        "/api/student/bookings",
        headers=headers(csrf, "first"),
        json={
            "start_at": "2026-07-20T14:00:00Z",
            "focus": "Quadratics",
            "confirmed": True,
        },
    )
    retried = await student.post(
        "/api/student/bookings",
        headers=headers(csrf, "first"),
        json={
            "start_at": "2026-07-20T14:00:00Z",
            "focus": "Quadratics",
            "confirmed": True,
        },
    )
    second_upcoming = await student.post(
        "/api/student/bookings",
        headers=headers(csrf, "second"),
        json={
            "start_at": "2026-07-20T15:00:00Z",
            "focus": None,
            "confirmed": True,
        },
    )

    assert created.status_code == retried.status_code == 201
    assert retried.json()["id"] == created.json()["id"]
    assert created.json()["funding_kind"] == "session_credit"
    assert "price_cents" not in created.json() and "currency" not in created.json()
    assert second_upcoming.status_code == 409
    assert (await student.get("/api/student/funding")).json() == {"session_credits": 0}

    clock[0] = datetime(2026, 7, 20, 15, 0, 1, tzinfo=timezone.utc)
    assert (await student.get("/api/student/funding")).json() == {"session_credits": 1}
    calendar = await tutor.get("/api/tutor/bookings")
    assert calendar.json()["bookings"][0]["status"] == "past"

    next_booking = await student.post(
        "/api/student/bookings",
        headers=headers(csrf, "next"),
        json={
            "start_at": "2026-07-27T14:00:00Z",
            "focus": None,
            "confirmed": True,
        },
    )
    assert next_booking.status_code == 201


@pytest.mark.anyio
async def test_repeated_and_concurrent_reconciliation_restores_once(testbed) -> None:
    _, _, student, _, database_url, clock = await booking_context(testbed)
    raw_session = student.cookies["tutoring_session"]
    testbed.seed(
        database_url,
        "INSERT INTO bookings "
        "(id, student_account_id, start_at, end_at, status, funding_kind, "
        "idempotency_key, created_at) VALUES "
        "('past-due', 'student', '2026-07-20 14:00:00', "
        "'2026-07-20 15:00:00', 'upcoming', 'session_credit', "
        "'past-due', CURRENT_TIMESTAMP)",
        "INSERT INTO credit_ledger_entries "
        "(id, student_account_id, event_type, quantity, reason, "
        "idempotency_key, created_at) VALUES "
        "('spent', 'student', 'credit_booking_redemption', -1, "
        "'Booking funding', 'spent', CURRENT_TIMESTAMP)",
    )
    clock[0] = datetime(2026, 7, 20, 15, 0, 1, tzinfo=timezone.utc)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(
            executor.map(
                lambda _: student_funding_summary(database_url, raw_session, clock[0]),
                range(8),
            )
        )

    assert results == [{"session_credits": 1}] * 8
    assert testbed.fetch_one(
        database_url,
        "SELECT COUNT(*) FROM credit_ledger_entries "
        "WHERE idempotency_key = 'booking:past-due:completion'",
    ) == 1
    assert testbed.fetch_one(
        database_url, "SELECT COUNT(*) FROM bookings WHERE status = 'past'"
    ) == 1


@pytest.mark.anyio
async def test_student_and_tutor_cancellation_restore_credit_once(testbed) -> None:
    tutor, tutor_csrf, student, student_csrf, database_url, _ = await booking_context(testbed)
    created = await student.post(
        "/api/student/bookings",
        headers=headers(student_csrf, "student-booking"),
        json={"start_at": "2026-07-20T14:00:00Z", "focus": None, "confirmed": True},
    )
    booking_id = created.json()["id"]
    cancelled = await student.post(
        f"/api/student/bookings/{booking_id}/cancel",
        headers=headers(student_csrf, "student-cancel"),
    )
    retried = await student.post(
        f"/api/student/bookings/{booking_id}/cancel",
        headers=headers(student_csrf, "student-cancel"),
    )
    assert cancelled.status_code == retried.status_code == 200
    assert (await student.get("/api/student/funding")).json() == {"session_credits": 1}

    created_again = await student.post(
        "/api/student/bookings",
        headers=headers(student_csrf, "tutor-booking"),
        json={"start_at": "2026-07-20T15:00:00Z", "focus": None, "confirmed": True},
    )
    tutor_cancelled = await tutor.post(
        f"/api/tutor/bookings/{created_again.json()['id']}/cancel",
        headers=headers(tutor_csrf, "tutor-cancel"),
    )
    assert tutor_cancelled.status_code == 200
    assert (await student.get("/api/student/funding")).json() == {"session_credits": 1}
    assert testbed.fetch_one(
        database_url,
        "SELECT COUNT(*) FROM credit_ledger_entries "
        "WHERE event_type = 'credit_booking_cancellation'",
    ) == 2


@pytest.mark.anyio
async def test_complimentary_cancellation_does_not_change_credit(testbed) -> None:
    tutor, tutor_csrf, _, _, database_url, _ = await booking_context(testbed)
    created = await tutor.post(
        "/api/tutor/students/student-2/bookings",
        headers=headers(tutor_csrf, "gift"),
        json={
            "start_at": "2026-07-20T14:00:00Z",
            "focus": "Tutor gift",
            "complimentary": True,
        },
    )
    cancelled = await tutor.post(
        f"/api/tutor/bookings/{created.json()['id']}/cancel",
        headers=headers(tutor_csrf, "cancel-gift"),
    )

    assert created.json()["funding_kind"] == "complimentary"
    assert cancelled.status_code == 200
    assert testbed.fetch_one(
        database_url,
        "SELECT COALESCE(SUM(quantity), 0) FROM credit_ledger_entries "
        "WHERE student_account_id = 'student-2'",
    ) == 0


@pytest.mark.anyio
async def test_tutor_edits_only_upcoming_bookings_and_past_records_remain(testbed) -> None:
    tutor, tutor_csrf, student, student_csrf, database_url, clock = await booking_context(testbed)
    created = await student.post(
        "/api/student/bookings",
        headers=headers(student_csrf, "history"),
        json={"start_at": "2026-07-20T14:00:00Z", "focus": None, "confirmed": True},
    )
    booking_id = created.json()["id"]
    details = await tutor.put(
        f"/api/tutor/bookings/{booking_id}/meeting-details",
        headers=headers(tutor_csrf, "unused"),
        json={"meeting_details": "Updated room"},
    )
    moved = await tutor.put(
        f"/api/tutor/bookings/{booking_id}/schedule",
        headers=headers(tutor_csrf, "unused"),
        json={"start_at": "2026-07-20T15:00:00Z"},
    )
    assert details.status_code == moved.status_code == 200

    clock[0] = datetime(2026, 7, 20, 16, 0, 1, tzinfo=timezone.utc)
    calendar = await tutor.get("/api/tutor/bookings")
    past_edit = await tutor.put(
        f"/api/tutor/bookings/{booking_id}/meeting-details",
        headers=headers(tutor_csrf, "unused"),
        json={"meeting_details": "Too late"},
    )
    past_move = await tutor.put(
        f"/api/tutor/bookings/{booking_id}/schedule",
        headers=headers(tutor_csrf, "unused"),
        json={"start_at": "2026-07-27T14:00:00Z"},
    )
    past_cancel = await tutor.post(
        f"/api/tutor/bookings/{booking_id}/cancel",
        headers=headers(tutor_csrf, "past-cancel"),
    )

    assert calendar.json()["bookings"][0]["status"] == "past"
    assert past_edit.status_code == past_move.status_code == past_cancel.status_code == 409
    assert testbed.fetch_one(
        database_url, f"SELECT COUNT(*) FROM bookings WHERE id = '{booking_id}'"
    ) == 1


@pytest.mark.anyio
async def test_student_reschedule_keeps_funding_and_twenty_four_hour_cutoff(testbed) -> None:
    _, _, student, csrf, database_url, clock = await booking_context(testbed)
    created = await student.post(
        "/api/student/bookings",
        headers=headers(csrf, "move-booking"),
        json={"start_at": "2026-07-20T14:00:00Z", "focus": "Algebra", "confirmed": True},
    )
    booking_id = created.json()["id"]
    moved = await student.put(
        f"/api/student/bookings/{booking_id}/schedule",
        headers=headers(csrf, "move"),
        json={"start_at": "2026-07-20T15:00:00Z"},
    )
    export = await student.get(f"/api/student/bookings/{booking_id}/calendar.ics")
    clock[0] = datetime(2026, 7, 19, 16, 0, 1, tzinfo=timezone.utc)
    late_move = await student.put(
        f"/api/student/bookings/{booking_id}/schedule",
        headers=headers(csrf, "late-move"),
        json={"start_at": "2026-07-27T14:00:00Z"},
    )

    assert moved.status_code == 200
    assert moved.json()["funding_kind"] == "session_credit"
    assert export.status_code == 200
    assert f"UID:{booking_id}@tutoring-platform" in export.text
    assert late_move.status_code == 409
    assert testbed.fetch_one(
        database_url,
        "SELECT COUNT(*) FROM credit_ledger_entries "
        "WHERE event_type = 'credit_booking_redemption'",
    ) == 1
