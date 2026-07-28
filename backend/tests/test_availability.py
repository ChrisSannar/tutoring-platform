from datetime import datetime, timezone

import httpx
import pytest


async def availability_clients(testbed):
    database_url = testbed.migrated("availability")
    testbed.seed(
        database_url,
        "INSERT INTO accounts (id, email, role, display_name) VALUES "
        "('tutor', 'tutor@example.com', 'tutor', NULL), "
        "('student', 'student@example.com', 'student', 'Student')",
    )
    app = testbed.app(now=lambda: datetime(2026, 7, 19, 8, tzinfo=timezone.utc))
    transport = httpx.ASGITransport(app=app)
    tutor, tutor_csrf = await testbed.authenticate(
        transport, database_url, "tutor@example.com"
    )
    student, _ = await testbed.authenticate(
        transport, database_url, "student@example.com"
    )
    return tutor, tutor_csrf, student, database_url


@pytest.mark.anyio
async def test_slots_are_anchored_blocked_and_privacy_preserving(testbed) -> None:
    tutor, csrf, student, _ = await availability_clients(testbed)

    created = await tutor.post(
        "/api/tutor/availability-windows",
        headers={"Origin": "http://testserver", "X-CSRF-Token": csrf},
        json={"weekday": 0, "start_time": "09:00", "end_time": "11:30"},
    )
    blocked = await tutor.post(
        "/api/tutor/blocked-times",
        headers={"Origin": "http://testserver", "X-CSRF-Token": csrf},
        json={
            "start_at": "2026-07-20T15:00:00Z",
            "end_at": "2026-07-20T16:00:00Z",
            "reason": "Private appointment",
        },
    )
    slots = await student.get("/api/student/bookable-slots")
    denied = await student.get("/api/tutor/availability-windows")

    assert created.status_code == blocked.status_code == 201
    assert slots.status_code == 200
    assert slots.json()["tutor_timezone"] == "America/Chicago"
    assert slots.json()["slots"][0] == {
        "start_at": "2026-07-20T14:00:00Z",
        "end_at": "2026-07-20T15:00:00Z",
    }
    assert all("reason" not in slot for slot in slots.json()["slots"])
    assert denied.status_code == 401


@pytest.mark.anyio
async def test_tutor_edits_and_deletes_calendar_rules(testbed) -> None:
    tutor, csrf, student, _ = await availability_clients(testbed)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf}

    window = await tutor.post(
        "/api/tutor/availability-windows", headers=headers,
        json={"weekday": 1, "start_time": "10:00", "end_time": "12:00"},
    )
    changed_window = await tutor.put(
        f"/api/tutor/availability-windows/{window.json()['id']}", headers=headers,
        json={"weekday": 2, "start_time": "11:00", "end_time": "13:00"},
    )
    blocked = await tutor.post(
        "/api/tutor/blocked-times", headers=headers,
        json={"start_at": "2026-07-22T16:00:00Z", "end_at": "2026-07-22T17:00:00Z", "reason": "Original"},
    )
    changed_block = await tutor.put(
        f"/api/tutor/blocked-times/{blocked.json()['id']}", headers=headers,
        json={"start_at": "2026-07-22T17:00:00Z", "end_at": "2026-07-22T18:00:00Z", "reason": "Private change"},
    )
    listed_blocks = await tutor.get("/api/tutor/blocked-times")
    removed_window = await tutor.delete(
        f"/api/tutor/availability-windows/{window.json()['id']}", headers=headers
    )
    removed_block = await tutor.delete(
        f"/api/tutor/blocked-times/{blocked.json()['id']}", headers=headers
    )
    student_mutation = await student.post(
        "/api/tutor/availability-windows", headers=headers,
        json={"weekday": 1, "start_time": "10:00", "end_time": "12:00"},
    )

    assert changed_window.json()["weekday"] == 2
    assert changed_block.json()["reason"] == "Private change"
    assert listed_blocks.json()[0]["reason"] == "Private change"
    assert removed_window.status_code == removed_block.status_code == 204
    assert student_mutation.status_code == 403


@pytest.mark.anyio
async def test_bookings_and_policy_boundaries_remove_slots(testbed) -> None:
    tutor, csrf, student, database_url = await availability_clients(testbed)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf}

    await tutor.post(
        "/api/tutor/availability-windows", headers=headers,
        json={"weekday": 0, "start_time": "09:00", "end_time": "12:00"},
    )
    await tutor.post(
        "/api/tutor/availability-windows", headers=headers,
        json={"weekday": 6, "start_time": "09:00", "end_time": "10:00"},
    )
    testbed.seed(
        database_url,
        "INSERT INTO bookings (id, student_account_id, start_at, end_at, status, funding_kind, idempotency_key, created_at) "
        "VALUES ('booking', 'student', '2026-07-20 14:00:00', '2026-07-20 15:00:00', 'upcoming', 'complimentary', 'booking', CURRENT_TIMESTAMP)",
    )
    slots = await student.get("/api/student/bookable-slots")

    starts = [slot["start_at"] for slot in slots.json()["slots"]]
    assert "2026-07-20T14:00:00Z" not in starts
    assert "2026-07-20T15:00:00Z" in starts
    assert "2026-07-20T16:00:00Z" in starts
    assert "2026-07-19T14:00:00Z" not in starts


@pytest.mark.anyio
async def test_tutor_override_records_an_explicit_booking_warning(testbed) -> None:
    tutor, csrf, student, _ = await availability_clients(testbed)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf}

    created = await tutor.post(
        "/api/tutor/overrides", headers=headers,
        json={"start_at": "2026-09-20T15:00:00Z", "warning": "Outside normal availability and horizon"},
    )
    listed = await tutor.get("/api/tutor/overrides")
    updated = await tutor.put(
        f"/api/tutor/overrides/{created.json()['id']}", headers=headers,
        json={"start_at": "2026-09-21T16:00:00Z", "warning": "Updated exception warning"},
    )
    denied = await student.get("/api/tutor/overrides")
    removed = await tutor.delete(
        f"/api/tutor/overrides/{created.json()['id']}", headers=headers
    )

    assert created.status_code == 201
    assert created.json()["requires_booking_warning"] is True
    assert listed.json()[0]["warning"] == "Outside normal availability and horizon"
    assert updated.status_code == 200
    assert updated.json()["start_at"] == "2026-09-21T16:00:00Z"
    assert updated.json()["end_at"] == "2026-09-21T17:00:00Z"
    assert updated.json()["warning"] == "Updated exception warning"
    assert updated.json()["requires_booking_warning"] is True
    assert denied.status_code == 401
    assert removed.status_code == 204
