from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
import socket
import subprocess
import sys
import threading
import time
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.authentication import issue_magic_link


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
        "INSERT INTO credit_ledger_entries (id, student_account_id, event_type, quantity, reason, idempotency_key, created_at) VALUES "
        "('promotion', 'student', 'promotion_granted', 1, NULL, 'promotion', CURRENT_TIMESTAMP), "
        "('credit', 'student', 'credit_adjustment', 1, 'Prepaid', 'credit', CURRENT_TIMESTAMP)",
        "UPDATE tutor_settings SET default_meeting_details = 'Initial meeting room' WHERE id = 1",
    )
    app = testbed.app(now=lambda: datetime(2026, 7, 19, 8, tzinfo=timezone.utc))
    transport = httpx.ASGITransport(app=app)
    tutor, tutor_csrf = await testbed.authenticate(
        transport, database_url, "tutor@example.com"
    )
    student, student_csrf = await testbed.authenticate(
        transport, database_url, "student@example.com"
    )
    return tutor, tutor_csrf, student, student_csrf, database_url


@pytest.mark.anyio
async def test_promotion_then_credit_booking_snapshots_settings(testbed) -> None:
    tutor, tutor_csrf, student, student_csrf, database_url = await booking_context(testbed)
    student_headers = {"Origin": "http://testserver", "X-CSRF-Token": student_csrf, "Idempotency-Key": "first-booking"}

    promotion = await student.post(
        "/api/student/bookings", headers=student_headers,
        json={"start_at": "2026-07-20T14:00:00Z", "focus": "Quadratic equations", "confirmed": True},
    )
    retry = await student.post(
        "/api/student/bookings", headers=student_headers,
        json={"start_at": "2026-07-20T14:00:00Z", "focus": "Quadratic equations", "confirmed": True},
    )
    funding_after_promotion = await student.get("/api/student/funding")
    await tutor.put(
        "/api/tutor/settings",
        headers={"Origin": "http://testserver", "X-CSRF-Token": tutor_csrf},
        json={"currency": "USD", "session_price_cents": 9000, "tutor_timezone": "America/Chicago", "default_meeting_details": "Changed room"},
    )
    unchanged = await student.get("/api/student/bookings/upcoming")
    testbed.seed(database_url, "UPDATE bookings SET status = 'completed'")
    credit = await student.post(
        "/api/student/bookings",
        headers={**student_headers, "Idempotency-Key": "credit-booking"},
        json={"start_at": "2026-07-20T15:00:00Z", "focus": None, "confirmed": True},
    )

    assert promotion.status_code == retry.status_code == 201
    assert promotion.json()["funding_kind"] == "first_session_promotion"
    assert retry.json()["id"] == promotion.json()["id"]
    assert funding_after_promotion.json() == {
        "first_session_promotion": "unavailable",
        "session_credits": 1,
    }
    assert unchanged.json()["meeting_details"] == "Initial meeting room"
    assert unchanged.json()["price_cents"] == 7500
    assert credit.status_code == 201
    assert credit.json()["funding_kind"] == "session_credit"
    assert credit.json()["meeting_details"] == "Changed room"
    assert credit.json()["price_cents"] == 9000


def test_live_concurrent_bookings_cannot_duplicate_slot_or_funding(testbed) -> None:
    now = datetime.now(timezone.utc)
    tutor_zone = ZoneInfo("America/Chicago")
    local_today = now.astimezone(tutor_zone).date()
    days_until_monday = (7 - local_today.weekday()) % 7
    race_day = local_today + timedelta(days=days_until_monday)
    first_slot = datetime.combine(
        race_day, datetime.min.time().replace(hour=9), tutor_zone
    )
    if first_slot.astimezone(timezone.utc) < now + timedelta(hours=24):
        first_slot += timedelta(days=7)
    race_slots = [
        (first_slot + timedelta(hours=offset))
        .astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
        for offset in range(5)
    ]
    database_url = testbed.database_url("live-bookings")
    testbed.migrate(database_url)
    testbed.seed(
        database_url,
        "INSERT INTO accounts (id, email, role, display_name) VALUES "
        "('tutor', 'tutor@example.com', 'tutor', NULL), "
        "('same-a', 'same-a@example.com', 'student', 'Same A'), "
        "('same-b', 'same-b@example.com', 'student', 'Same B'), "
        "('credit-racer', 'credit-racer@example.com', 'student', 'Credit Racer')",
        "INSERT INTO availability_windows (id, weekday, start_time, end_time) "
        "VALUES ('race-monday', 0, '09:00', '17:00')",
        "INSERT INTO credit_ledger_entries "
        "(id, student_account_id, event_type, quantity, reason, idempotency_key, created_at) VALUES "
        "('same-a-promotion', 'same-a', 'promotion_granted', 1, NULL, 'same-a-promotion', CURRENT_TIMESTAMP), "
        "('same-b-promotion', 'same-b', 'promotion_granted', 1, NULL, 'same-b-promotion', CURRENT_TIMESTAMP), "
        "('credit-racer-credit', 'credit-racer', 'credit_adjustment', 1, 'Prepaid', 'credit-racer-credit', CURRENT_TIMESTAMP)",
    )

    with socket.socket() as available_port:
        available_port.bind(("127.0.0.1", 0))
        port = available_port.getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"
    testbed.setenv(database_url, origin=base_url)
    tokens = {
        student: issue_magic_link(database_url, f"{student}@example.com", 900)
        for student in ("same-a", "same-b", "credit-racer")
    }
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--workers",
            "2",
            "--no-access-log",
        ],
        cwd="backend",
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        for _ in range(100):
            try:
                if httpx.get(f"{base_url}/api/health").status_code == 200:
                    break
            except httpx.ConnectError:
                time.sleep(0.05)
        else:
            raise AssertionError("live HTTP test server did not start")

        sessions = {}
        for student, token in tokens.items():
            authenticated = httpx.post(
                f"{base_url}/api/auth/magic-links/confirm", json={"token": token}
            )
            sessions[student] = (
                dict(authenticated.cookies),
                authenticated.json()["csrf_token"],
            )

        def race(attempts):
            barrier = threading.Barrier(2)

            def submit(student: str, start_at: str, key: str):
                cookies, csrf = sessions[student]
                barrier.wait()
                request_started = time.monotonic()
                response = httpx.post(
                    f"{base_url}/api/student/bookings",
                    headers={
                        "Origin": base_url,
                        "X-CSRF-Token": csrf,
                        "Idempotency-Key": key,
                    },
                    cookies=cookies,
                    json={"start_at": start_at, "focus": None, "confirmed": True},
                )
                return response, request_started, time.monotonic()

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(submit, *attempt) for attempt in attempts]
                results = [future.result(timeout=10) for future in futures]
            assert max(result[1] for result in results) < min(
                result[2] for result in results
            )
            return [result[0] for result in results]

        same_slot = race([
            ("same-a", race_slots[0], "same-slot-a"),
            ("same-b", race_slots[0], "same-slot-b"),
        ])
        promotion_racer = (
            "same-a" if same_slot[0].status_code == 409 else "same-b"
        )
        promotion = race([
            (promotion_racer, race_slots[1], "promotion-one"),
            (promotion_racer, race_slots[2], "promotion-two"),
        ])
        credit = race([
            ("credit-racer", race_slots[3], "credit-one"),
            ("credit-racer", race_slots[4], "credit-two"),
        ])
        promotion_funding = httpx.get(
            f"{base_url}/api/student/funding",
            cookies=sessions[promotion_racer][0],
        )
        credit_funding = httpx.get(
            f"{base_url}/api/student/funding",
            cookies=sessions["credit-racer"][0],
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)

    assert sorted(response.status_code for response in same_slot) == [201, 409]
    assert sorted(response.status_code for response in promotion) == [201, 409]
    assert sorted(response.status_code for response in credit) == [201, 409]
    assert promotion_funding.json()["first_session_promotion"] == "unavailable"
    assert credit_funding.json()["session_credits"] == 0


@pytest.mark.anyio
async def test_tutor_creates_explicit_complimentary_booking_without_funding(testbed) -> None:
    tutor, tutor_csrf, student, _, _ = await booking_context(testbed)

    created = await tutor.post(
        "/api/tutor/students/student-2/bookings",
        headers={"Origin": "http://testserver", "X-CSRF-Token": tutor_csrf, "Idempotency-Key": "gift"},
        json={"start_at": "2026-07-20T16:00:00Z", "focus": "Tutor gift", "complimentary": True},
    )
    student_denied = await student.post(
        "/api/tutor/students/student-2/bookings",
        headers={"Origin": "http://testserver", "X-CSRF-Token": tutor_csrf, "Idempotency-Key": "denied"},
        json={"start_at": "2026-07-20T16:00:00Z", "focus": None, "complimentary": True},
    )

    assert created.status_code == 201
    assert created.json()["funding_kind"] == "complimentary"
    assert student_denied.status_code == 403


@pytest.mark.anyio
async def test_override_requires_warning_and_unfunded_student_cannot_book(testbed) -> None:
    tutor, tutor_csrf, student, _, database_url = await booking_context(testbed)
    tutor_headers = {"Origin": "http://testserver", "X-CSRF-Token": tutor_csrf}
    second, second_csrf = await testbed.authenticate(
        httpx.ASGITransport(
            app=testbed.app(now=lambda: datetime(2026, 7, 19, 8, tzinfo=timezone.utc))
        ),
        database_url,
        "second@example.com",
    )
    second_headers = {"Origin": "http://testserver", "X-CSRF-Token": second_csrf, "Idempotency-Key": "unfunded"}

    unfunded = await second.post(
        "/api/student/bookings", headers=second_headers,
        json={"start_at": "2026-07-20T14:00:00Z", "focus": None, "confirmed": True},
    )
    override = await tutor.post(
        "/api/tutor/overrides", headers=tutor_headers,
        json={"start_at": "2026-09-20T15:00:00Z", "warning": "Outside normal policy"},
    )
    without_warning = await tutor.post(
        "/api/tutor/students/student-2/bookings",
        headers={**tutor_headers, "Idempotency-Key": "override-no-warning"},
        json={"start_at": "2026-09-20T15:00:00Z", "focus": None, "complimentary": True, "override_id": override.json()["id"]},
    )
    with_warning = await tutor.post(
        "/api/tutor/students/student-2/bookings",
        headers={**tutor_headers, "Idempotency-Key": "override-warning"},
        json={"start_at": "2026-09-20T15:00:00Z", "focus": None, "complimentary": True, "override_id": override.json()["id"], "warning_acknowledged": True},
    )

    assert unfunded.status_code == 409
    assert without_warning.status_code == 409
    assert with_warning.status_code == 201


@pytest.mark.anyio
async def test_tutor_calendar_edits_and_moves_booking_without_changing_funding(testbed) -> None:
    tutor, tutor_csrf, student, student_csrf, database_url = await booking_context(testbed)
    tutor_headers = {"Origin": "http://testserver", "X-CSRF-Token": tutor_csrf}

    created = await student.post(
        "/api/student/bookings",
        headers={"Origin": "http://testserver", "X-CSRF-Token": student_csrf, "Idempotency-Key": "calendar-booking"},
        json={"start_at": "2026-07-20T14:00:00Z", "focus": "Fractions", "confirmed": True},
    )
    calendar = await tutor.get("/api/tutor/bookings")
    booking_id = created.json()["id"]
    details = await tutor.put(
        f"/api/tutor/bookings/{booking_id}/meeting-details", headers=tutor_headers,
        json={"meeting_details": "123 Main Street"},
    )
    moved = await tutor.put(
        f"/api/tutor/bookings/{booking_id}/schedule", headers=tutor_headers,
        json={"start_at": "2026-07-20T15:00:00Z"},
    )
    await tutor.post(
        "/api/tutor/students/student-2/bookings",
        headers={**tutor_headers, "Idempotency-Key": "occupied"},
        json={"start_at": "2026-07-20T16:00:00Z", "focus": None, "complimentary": True},
    )
    conflict = await tutor.put(
        f"/api/tutor/bookings/{booking_id}/schedule", headers=tutor_headers,
        json={"start_at": "2026-07-20T16:00:00Z"},
    )
    override = await tutor.post(
        "/api/tutor/overrides", headers=tutor_headers,
        json={"start_at": "2026-09-20T15:00:00Z", "warning": "Outside normal policy"},
    )
    unacknowledged = await tutor.put(
        f"/api/tutor/bookings/{booking_id}/schedule", headers=tutor_headers,
        json={"start_at": "2026-09-20T15:00:00Z", "override_id": override.json()["id"]},
    )
    overridden = await tutor.put(
        f"/api/tutor/bookings/{booking_id}/schedule", headers=tutor_headers,
        json={"start_at": "2026-09-20T15:00:00Z", "override_id": override.json()["id"], "warning_acknowledged": True},
    )
    denied = await student.get("/api/tutor/bookings")
    funding_events = testbed.fetch_all(
        database_url,
        "SELECT event_type, quantity FROM credit_ledger_entries WHERE student_account_id = 'student' ORDER BY created_at, id",
    )

    assert calendar.json()["bookings"][0]["student"]["display_name"] == "Student"
    assert details.json()["meeting_details"] == "123 Main Street"
    assert moved.json()["funding_kind"] == "first_session_promotion"
    assert conflict.status_code == 409
    assert unacknowledged.status_code == 409
    assert overridden.status_code == 200
    assert overridden.json()["funding_kind"] == "first_session_promotion"
    assert denied.status_code == 401
    assert [event for event in funding_events if event[0] == "promotion_consumed"] == [("promotion_consumed", -1)]


@pytest.mark.anyio
async def test_student_reschedule_explicitly_excludes_its_booking_from_occupancy(
    testbed,
) -> None:
    tutor, _, student, student_csrf, _ = await booking_context(testbed)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": student_csrf}

    created = await student.post(
        "/api/student/bookings",
        headers={**headers, "Idempotency-Key": "self-exclusion-booking"},
        json={
            "start_at": "2026-07-20T14:00:00Z",
            "focus": None,
            "confirmed": True,
        },
    )
    rescheduled = await student.put(
        f"/api/student/bookings/{created.json()['id']}/schedule",
        headers={**headers, "Idempotency-Key": "self-exclusion-move"},
        json={"start_at": "2026-07-20T09:00:00-05:00"},
    )

    assert created.status_code == 201
    assert rescheduled.status_code == 200
    assert rescheduled.json()["start_at"] == "2026-07-20T14:00:00Z"


@pytest.mark.anyio
async def test_student_reschedules_exports_and_cancels_with_funding_restoration(testbed) -> None:
    tutor, _, student, student_csrf, database_url = await booking_context(testbed)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": student_csrf}

    created = await student.post(
        "/api/student/bookings",
        headers={**headers, "Idempotency-Key": "change-booking"},
        json={"start_at": "2026-07-20T14:00:00Z", "focus": "Commas, semicolons; and newlines\nnext", "confirmed": True},
    )
    booking_id = created.json()["id"]
    moved = await student.put(
        f"/api/student/bookings/{booking_id}/schedule",
        headers={**headers, "Idempotency-Key": "student-move"},
        json={"start_at": "2026-07-20T15:00:00Z"},
    )
    retried = await student.put(
        f"/api/student/bookings/{booking_id}/schedule",
        headers={**headers, "Idempotency-Key": "student-move"},
        json={"start_at": "2026-07-20T15:00:00Z"},
    )
    moved_again = await student.put(
        f"/api/student/bookings/{booking_id}/schedule",
        headers={**headers, "Idempotency-Key": "student-move-again"},
        json={"start_at": "2026-07-20T16:00:00Z"},
    )
    exported = await student.get(f"/api/student/bookings/{booking_id}/calendar.ics")
    other, other_csrf = await testbed.authenticate(
        httpx.ASGITransport(
            app=testbed.app(now=lambda: datetime(2026, 7, 19, 8, tzinfo=timezone.utc))
        ),
        database_url,
        "second@example.com",
    )
    other_export = await other.get(f"/api/student/bookings/{booking_id}/calendar.ics")
    other_move = await other.put(
        f"/api/student/bookings/{booking_id}/schedule",
        headers={"Origin": "http://testserver", "X-CSRF-Token": other_csrf, "Idempotency-Key": "other-move"},
        json={"start_at": "2026-07-20T16:00:00Z"},
    )
    cancelled = await student.post(
        f"/api/student/bookings/{booking_id}/cancel",
        headers={**headers, "Idempotency-Key": "student-cancel"},
        json={"forfeit_funding": False},
    )
    cancel_retry = await student.post(
        f"/api/student/bookings/{booking_id}/cancel",
        headers={**headers, "Idempotency-Key": "student-cancel"},
        json={"forfeit_funding": False},
    )
    funding = await student.get("/api/student/funding")

    assert moved.status_code == retried.status_code == 200
    assert moved_again.status_code == 200
    assert moved.json()["start_at"] == "2026-07-20T15:00:00Z"
    assert moved.json()["funding_kind"] == "first_session_promotion"
    assert exported.status_code == 200
    assert exported.headers["content-disposition"] == 'attachment; filename="tutoring-session-2026-07-20.ics"'
    assert f"UID:{booking_id}@tutoring-platform" in exported.text
    assert "DTSTART;TZID=America/Chicago:20260720T110000" in exported.text
    assert "Commas\\, semicolons\\; and newlines\\nnext" in exported.text
    assert other_export.status_code == 404
    assert other_move.status_code == 409
    assert cancelled.status_code == cancel_retry.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert funding.json()["first_session_promotion"] == "available"


@pytest.mark.anyio
async def test_student_change_policy_is_exact_at_twenty_four_hours(testbed) -> None:
    tutor, _, student, student_csrf, database_url = await booking_context(testbed)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": student_csrf}

    created = await student.post(
        "/api/student/bookings",
        headers={**headers, "Idempotency-Key": "boundary-booking"},
        json={"start_at": "2026-07-20T14:00:00Z", "focus": None, "confirmed": True},
    )
    booking_id = created.json()["id"]
    testbed.seed(
        database_url,
        (
            "UPDATE bookings SET start_at = '2026-07-20 08:00:00', end_at = '2026-07-20 09:00:00' WHERE id = :id",
            {"id": booking_id},
        ),
    )
    exact = await student.post(
        f"/api/student/bookings/{booking_id}/cancel",
        headers={**headers, "Idempotency-Key": "exact-cancel"},
        json={"forfeit_funding": False},
    )
    testbed.seed(
        database_url,
        (
            "UPDATE bookings SET status = 'upcoming', start_at = '2026-07-20 07:59:59', end_at = '2026-07-20 08:59:59' WHERE id = :id",
            {"id": booking_id},
        ),
    )
    inside_without_confirmation = await student.post(
        f"/api/student/bookings/{booking_id}/cancel",
        headers={**headers, "Idempotency-Key": "late-no-confirm"},
        json={"forfeit_funding": False},
    )
    inside_confirmed = await student.post(
        f"/api/student/bookings/{booking_id}/cancel",
        headers={**headers, "Idempotency-Key": "late-confirmed"},
        json={"forfeit_funding": True},
    )

    assert exact.status_code == 200
    assert inside_without_confirmation.status_code == 409
    assert inside_confirmed.status_code == 200


@pytest.mark.anyio
async def test_early_paid_cancellation_grants_one_replacement_credit(testbed) -> None:
    tutor, _, student, student_csrf, database_url = await booking_context(testbed)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": student_csrf}

    created = await student.post(
        "/api/student/bookings",
        headers={**headers, "Idempotency-Key": "future-paid"},
        json={"start_at": "2026-07-20T14:00:00Z", "focus": None, "confirmed": True},
    )
    testbed.seed(
        database_url,
        (
            "UPDATE bookings SET funding_kind = 'paid' WHERE id = :id",
            {"id": created.json()["id"]},
        ),
    )
    cancelled = await student.post(
        f"/api/student/bookings/{created.json()['id']}/cancel",
        headers={**headers, "Idempotency-Key": "paid-cancel"},
        json={"forfeit_funding": False},
    )
    restored = testbed.fetch_one(
        database_url,
        "SELECT quantity FROM credit_ledger_entries WHERE event_type = 'credit_paid_cancellation'",
    )

    assert cancelled.status_code == 200
    assert restored == 1
