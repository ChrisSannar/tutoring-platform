import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json

import httpx
import pytest

from app.checkout.provider import create_provider_checkout


async def checkout_clients(testbed, monkeypatch):
    database_url = testbed.migrated("checkout")
    testbed.seed(
        database_url,
        "INSERT INTO accounts (id, email, role, display_name) VALUES "
        "('student', 'student@example.com', 'student', 'Student'), "
        "('other', 'other@example.com', 'student', 'Other')",
        "INSERT INTO availability_windows (id, weekday, start_time, end_time) "
        "VALUES ('monday', 0, '09:00', '11:00')",
        "UPDATE tutor_settings SET session_price_cents = 8250, default_meeting_details = 'Paid room' WHERE id = 1",
    )
    monkeypatch.setenv("TUTORING_STRIPE_WEBHOOK_SECRET", "signed-test-secret")
    clock = [datetime(2026, 7, 19, 8, tzinfo=timezone.utc)]
    transport = httpx.ASGITransport(app=testbed.app(now=lambda: clock[0]))
    student, csrf = await testbed.authenticate(
        transport, database_url, "student@example.com"
    )
    other, other_csrf = await testbed.authenticate(
        transport, database_url, "other@example.com"
    )
    return student, csrf, other, other_csrf, database_url, clock


def signed_event(event: dict, timestamp: str = "1784448000") -> tuple[bytes, str]:
    body = json.dumps(event, separators=(",", ":")).encode()
    signature = hmac.new(
        b"signed-test-secret", timestamp.encode() + b"." + body, hashlib.sha256
    ).hexdigest()
    return body, f"t={timestamp},v1={signature}"


def test_stripe_checkout_adapter_uses_server_amount_and_metadata(monkeypatch) -> None:
    captured = {}

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def read(self): return b'{"id":"cs_live_one","url":"https://checkout.stripe.com/c/pay/one"}'

    def fake_urlopen(request, timeout):
        captured.update(url=request.full_url, headers=dict(request.header_items()), body=request.data, timeout=timeout)
        return Response()

    monkeypatch.setattr("app.checkout.provider.urlopen", fake_urlopen)
    provider_id, url = create_provider_checkout(
        "stripe", "sk_test_private", "https://tutor.example", 8250, "USD", "student", "2026-07-20T14:00:00Z"
    )
    fields = captured["body"].decode()

    assert (provider_id, url) == ("cs_live_one", "https://checkout.stripe.com/c/pay/one")
    assert captured["url"] == "https://api.stripe.com/v1/checkout/sessions"
    assert captured["headers"]["Authorization"] == "Bearer sk_test_private"
    assert "unit_amount%5D=8250" in fields and "currency%5D=usd" in fields
    assert "metadata%5Bstudent_id%5D=student" in fields
    assert "metadata%5Bstart_at%5D=2026-07-20T14%3A00%3A00Z" in fields


@pytest.mark.anyio
async def test_checkout_hold_status_only_return_and_signed_fulfillment(testbed, monkeypatch) -> None:
    student, csrf, other, _, database_url, _ = await checkout_clients(testbed, monkeypatch)
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf, "Idempotency-Key": "checkout-one"}

    tampered = await student.post(
        "/api/student/checkouts", headers={**headers, "Idempotency-Key": "tampered"},
        json={"start_at": "2026-07-20T14:00:00Z", "focus": "Paid lesson", "amount": 1},
    )
    checkout = await student.post(
        "/api/student/checkouts", headers=headers,
        json={"start_at": "2026-07-20T14:00:00Z", "focus": "Paid lesson"},
    )
    other_slots = await other.get("/api/student/bookable-slots")
    browser_return = await student.get(
        f"/api/student/checkouts/{checkout.json()['checkout_session_id']}"
    )
    before_webhook = testbed.fetch_one(database_url, "SELECT COUNT(*) FROM bookings")
    event = {
        "id": "evt_paid_one", "type": "checkout.session.completed",
        "data": {"object": {"id": checkout.json()["checkout_session_id"],
                 "metadata": {"student_id": "student", "start_at": "2026-07-20T14:00:00Z"},
                 "currency": "usd", "amount_total": 8250, "payment_intent": "pi_one"}},
    }
    body, signature = signed_event(event)
    invalid = await student.post("/api/stripe/webhook", content=body, headers={"Stripe-Signature": "wrong"})
    first, duplicate = await asyncio.gather(
        student.post("/api/stripe/webhook", content=body, headers={"Stripe-Signature": signature}),
        student.post("/api/stripe/webhook", content=body, headers={"Stripe-Signature": signature}),
    )
    bookings = testbed.fetch_all(database_url, "SELECT funding_kind, price_cents_snapshot FROM bookings")
    evidence = testbed.fetch_all(database_url, "SELECT provider_payment_id, amount_cents FROM payment_evidence")
    holds = testbed.fetch_one(database_url, "SELECT COUNT(*) FROM slot_holds")

    assert tampered.status_code == 422 and checkout.status_code == 201
    assert checkout.json()["amount_cents"] == 8250 and checkout.json()["currency"] == "USD"
    assert checkout.json()["checkout_url"].startswith("/checkout/fake/")
    assert all(slot["start_at"] != "2026-07-20T14:00:00Z" for slot in other_slots.json()["slots"])
    assert browser_return.json()["status"] == "pending" and before_webhook == 0
    assert invalid.status_code == 400
    assert sorted([first.status_code, duplicate.status_code]) == [200, 200]
    assert bookings == [("paid", 8250)]
    assert evidence == [("pi_one", 8250)] and holds == 0


@pytest.mark.anyio
async def test_checkout_mismatch_and_expiry_release_holds(testbed, monkeypatch) -> None:
    student, csrf, other, _, _, clock = await checkout_clients(testbed, monkeypatch)
    base = {"Origin": "http://testserver", "X-CSRF-Token": csrf}

    first = await student.post(
        "/api/student/checkouts", headers={**base, "Idempotency-Key": "mismatch"},
        json={"start_at": "2026-07-20T14:00:00Z", "focus": None},
    )
    mismatch_event = {"id": "evt_mismatch", "type": "checkout.session.completed", "data": {
        "id": first.json()["checkout_session_id"], "student_id": "student", "start_at": "2026-07-20T14:00:00Z",
        "currency": "USD", "amount_total": 1, "payment_intent": "pi_bad"}}
    body, signature = signed_event(mismatch_event)
    mismatch = await student.post("/api/stripe/webhook", content=body, headers={"Stripe-Signature": signature})
    released = await other.get("/api/student/bookable-slots")

    second = await student.post(
        "/api/student/checkouts", headers={**base, "Idempotency-Key": "expires"},
        json={"start_at": "2026-07-20T15:00:00Z", "focus": None},
    )
    clock[0] += timedelta(minutes=31)
    expired = await student.get(f"/api/student/checkouts/{second.json()['checkout_session_id']}")
    after_expiry = await other.get("/api/student/bookable-slots")

    reconciled_checkout = await student.post(
        "/api/student/checkouts", headers={**base, "Idempotency-Key": "provider-expiry"},
        json={"start_at": "2026-07-20T14:00:00Z", "focus": None},
    )
    expired_event = {"id": "evt_expired", "type": "checkout.session.expired", "data": {
        "object": {"id": reconciled_checkout.json()["checkout_session_id"]}}}
    expired_body, expired_signature = signed_event(expired_event, "1784449860")
    reconciled = await student.post(
        "/api/stripe/webhook", content=expired_body, headers={"Stripe-Signature": expired_signature}
    )
    after_reconciliation = await other.get("/api/student/bookable-slots")

    assert mismatch.status_code == 409
    assert any(slot["start_at"] == "2026-07-20T14:00:00Z" for slot in released.json()["slots"])
    assert expired.json()["status"] == "expired"
    assert any(slot["start_at"] == "2026-07-20T15:00:00Z" for slot in after_expiry.json()["slots"])
    assert reconciled.json() == {"status": "expired"}
    assert any(slot["start_at"] == "2026-07-20T14:00:00Z" for slot in after_reconciliation.json()["slots"])


@pytest.mark.anyio
async def test_concurrent_checkout_starts_create_only_one_hold(testbed, monkeypatch) -> None:
    student, csrf, other, other_csrf, database_url, _ = await checkout_clients(testbed, monkeypatch)
    payload = {"start_at": "2026-07-20T14:00:00Z", "focus": None}

    first, second = await asyncio.gather(
        student.post("/api/student/checkouts", headers={"Origin": "http://testserver", "X-CSRF-Token": csrf, "Idempotency-Key": "race-one"}, json=payload),
        other.post("/api/student/checkouts", headers={"Origin": "http://testserver", "X-CSRF-Token": other_csrf, "Idempotency-Key": "race-two"}, json=payload),
    )
    holds = testbed.fetch_one(database_url, "SELECT COUNT(*) FROM slot_holds")

    assert sorted([first.status_code, second.status_code]) == [201, 409]
    assert holds == 1
