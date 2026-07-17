import asyncio
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text

from app.authentication import issue_magic_link
from app.config import get_settings
from app.main import create_app
from app.refunds.provider import refund_payment


async def refund_clients(monkeypatch, tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'refunds.sqlite3'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO accounts (id, email, role, display_name) VALUES "
            "('tutor', 'tutor@example.com', 'tutor', NULL), "
            "('student', 'student@example.com', 'student', 'Student'), "
            "('other', 'other@example.com', 'student', 'Other')"
        ))
        for booking_id, student_id, payment_id in [
            ("paid-one", "student", "pi_paid_one"),
            ("paid-two", "student", "pi_paid_two"),
            ("other-paid", "other", "pi_other"),
        ]:
            connection.execute(text(
                "INSERT INTO bookings (id, student_account_id, start_at, end_at, status, funding_kind, "
                "price_cents_snapshot, currency_snapshot, idempotency_key, created_at) VALUES "
                "(:id, :student, '2026-07-25 14:00:00', '2026-07-25 15:00:00', 'cancelled', 'paid', "
                "8250, 'USD', :booking_key, CURRENT_TIMESTAMP)"
            ), {"id": booking_id, "student": student_id, "booking_key": f"booking:{booking_id}"})
            connection.execute(text(
                "INSERT INTO payment_evidence (id, booking_id, checkout_session_id, provider_payment_id, "
                "provider_event_id, amount_cents, currency, created_at) VALUES "
                "(:evidence, :booking, :checkout, :payment, :event, 8250, 'USD', CURRENT_TIMESTAMP)"
            ), {"evidence": f"evidence-{booking_id}", "booking": booking_id,
                "checkout": f"checkout-{booking_id}", "payment": payment_id, "event": f"event-{booking_id}"})
            connection.execute(text(
                "INSERT INTO credit_ledger_entries (id, student_account_id, event_type, quantity, reason, "
                "idempotency_key, created_at) VALUES (:id, :student, 'credit_paid_cancellation', 1, "
                "'Booking cancellation restoration', :key, CURRENT_TIMESTAMP)"
            ), {"id": f"credit-{booking_id}", "student": student_id, "key": f"cancel:{booking_id}"})
    engine.dispose()
    monkeypatch.setenv("TUTORING_ENVIRONMENT", "test")
    monkeypatch.setenv("TUTORING_DATABASE_URL", database_url)
    monkeypatch.setenv("TUTORING_APPLICATION_ORIGIN", "http://testserver")
    get_settings.cache_clear()
    app = create_app()
    app.state.context.now = lambda: datetime(2026, 7, 19, 8, tzinfo=timezone.utc)
    transport = httpx.ASGITransport(app=app)

    async def authenticate(email: str):
        client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
        token = issue_magic_link(database_url, email, 900)
        response = await client.post("/api/auth/magic-links/confirm", json={"token": token})
        return client, response.json()["csrf_token"]

    tutor, tutor_csrf = await authenticate("tutor@example.com")
    student, student_csrf = await authenticate("student@example.com")
    other, other_csrf = await authenticate("other@example.com")
    return app, tutor, tutor_csrf, student, student_csrf, other, other_csrf, database_url


def mutation(csrf: str, key: str) -> dict[str, str]:
    return {"Origin": "http://testserver", "X-CSRF-Token": csrf, "Idempotency-Key": key}


def test_stripe_refund_adapter_uses_full_server_amount_and_stable_key(monkeypatch) -> None:
    captured = {}

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def read(self): return b'{"id":"re_live_one","status":"succeeded"}'

    def fake_urlopen(request, timeout):
        captured.update(headers=dict(request.header_items()), body=request.data.decode(), timeout=timeout)
        return Response()

    monkeypatch.setattr("app.refunds.provider.urlopen", fake_urlopen)
    result = refund_payment("stripe", "sk_private", "pi_original", 8250, "USD", "request-one")

    assert result == (True, "re_live_one")
    assert captured["headers"]["Authorization"] == "Bearer sk_private"
    assert captured["headers"]["Idempotency-key"] == "request-one"
    assert captured["body"] == "payment_intent=pi_original&amount=8250"


@pytest.mark.anyio
async def test_refund_request_eligibility_ownership_freeze_and_decline(monkeypatch, tmp_path: Path) -> None:
    _, tutor, tutor_csrf, student, student_csrf, other, other_csrf, database_url = await refund_clients(monkeypatch, tmp_path)
    try:
        wrong_owner = await other.post("/api/student/bookings/paid-one/refund-request", headers=mutation(other_csrf, "wrong"))
        wrong_role = await tutor.post("/api/student/bookings/paid-one/refund-request", headers=mutation(tutor_csrf, "wrong-role"))
        created = await student.post("/api/student/bookings/paid-one/refund-request", headers=mutation(student_csrf, "request-one"))
        retried = await student.post("/api/student/bookings/paid-one/refund-request", headers=mutation(student_csrf, "request-one"))
        frozen = await student.get("/api/student/funding")
        student_queue = await student.get("/api/student/refund-requests")
        other_queue = await other.get("/api/student/refund-requests")
        tutor_queue = await tutor.get("/api/tutor/refund-requests")
        cross_role = await student.post(
            f"/api/tutor/refund-requests/{created.json()['id']}/decline", headers=mutation(student_csrf, "forbidden")
        )
        declined = await tutor.post(
            f"/api/tutor/refund-requests/{created.json()['id']}/decline", headers=mutation(tutor_csrf, "decline-one")
        )
        decline_retry = await tutor.post(
            f"/api/tutor/refund-requests/{created.json()['id']}/decline", headers=mutation(tutor_csrf, "decline-one")
        )
        restored = await student.get("/api/student/funding")
        engine = create_engine(database_url)
        with engine.connect() as connection:
            unfreezes = connection.execute(text(
                "SELECT COUNT(*) FROM credit_ledger_entries WHERE event_type = 'credit_refund_unfreeze'"
            )).scalar_one()
        engine.dispose()
    finally:
        await tutor.aclose(); await student.aclose(); await other.aclose(); get_settings.cache_clear()

    assert wrong_owner.status_code == 404
    assert wrong_role.status_code == 403
    assert created.status_code == 201 and retried.json()["id"] == created.json()["id"]
    assert frozen.json()["session_credits"] == 1
    assert [item["id"] for item in student_queue.json()["refund_requests"]] == [created.json()["id"]]
    assert other_queue.json()["refund_requests"] == []
    assert tutor_queue.json()["refund_requests"][0]["student"]["display_name"] == "Student"
    assert cross_role.status_code == 403
    assert declined.json()["status"] == "declined" and decline_retry.json()["status"] == "declined"
    assert restored.json()["session_credits"] == 2 and unfreezes == 1


@pytest.mark.anyio
async def test_full_refund_failure_retry_and_concurrent_review_are_exactly_once(monkeypatch, tmp_path: Path) -> None:
    app, tutor, tutor_csrf, student, student_csrf, _, _, database_url = await refund_clients(monkeypatch, tmp_path)
    calls = []

    def fail_once(payment_id: str, amount_cents: int, currency: str, key: str):
        calls.append((payment_id, amount_cents, currency, key))
        if len(calls) == 1: return False, None
        return True, "re_full_one" if payment_id == "pi_paid_one" else "re_full_two"

    app.state.context.refund_payment = fail_once
    try:
        created = await student.post("/api/student/bookings/paid-one/refund-request", headers=mutation(student_csrf, "request-approve"))
        failed = await tutor.post(
            f"/api/tutor/refund-requests/{created.json()['id']}/approve", headers=mutation(tutor_csrf, "approve-one")
        )
        pending = await student.get("/api/student/refund-requests")
        still_frozen = await student.get("/api/student/funding")
        approved = await tutor.post(
            f"/api/tutor/refund-requests/{created.json()['id']}/approve", headers=mutation(tutor_csrf, "approve-one")
        )
        retry = await tutor.post(
            f"/api/tutor/refund-requests/{created.json()['id']}/approve", headers=mutation(tutor_csrf, "approve-one")
        )
        second = await student.post(
            "/api/student/bookings/paid-two/refund-request", headers=mutation(student_csrf, "request-race")
        )
        competing_approve, competing_decline = await asyncio.gather(
            tutor.post(f"/api/tutor/refund-requests/{second.json()['id']}/approve", headers=mutation(tutor_csrf, "approve-race")),
            tutor.post(f"/api/tutor/refund-requests/{second.json()['id']}/decline", headers=mutation(tutor_csrf, "decline-race")),
        )
        final_funding = await student.get("/api/student/funding")
        engine = create_engine(database_url)
        with engine.connect() as connection:
            evidence = connection.execute(text(
                "SELECT provider_refund_id, amount_cents, currency FROM refund_evidence"
            )).all()
            unfreezes = connection.execute(text(
                "SELECT COUNT(*) FROM credit_ledger_entries WHERE event_type = 'credit_refund_unfreeze'"
            )).scalar_one()
        engine.dispose()
    finally:
        await tutor.aclose(); await student.aclose(); get_settings.cache_clear()

    assert failed.status_code == 502
    assert pending.json()["refund_requests"][0]["status"] == "pending"
    assert still_frozen.json()["session_credits"] == 1
    assert approved.json()["status"] == "refunded" and retry.json()["status"] == "refunded"
    assert sorted([competing_approve.status_code, competing_decline.status_code]) == [200, 409]
    assert calls[:2] == [("pi_paid_one", 8250, "USD", created.json()["id"])] * 2
    if competing_approve.status_code == 200:
        assert len(evidence) == 2 and unfreezes == 0
        assert final_funding.json()["session_credits"] == 0
    else:
        assert evidence == [("re_full_one", 8250, "USD")] and unfreezes == 1
        assert final_funding.json()["session_credits"] == 1
